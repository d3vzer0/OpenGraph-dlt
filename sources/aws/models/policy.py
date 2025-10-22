from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr
from sources.aws.models.graph import NodeProperties, Node
from sources.shared.models.entries import Edge, EdgePath, EdgeProperties
from sources.aws.utils.guid import NodeTypes, gen_guid
from sources.aws.utils.lookup import LookupManager
import fnmatch


def flatten_principals(principal_obj: dict) -> list[str]:
    principals: list[str] = []
    for key, value in principal_obj.items():
        if isinstance(value, list):
            principals.extend(value)
        elif isinstance(value, str):
            principals.append(value)
        elif isinstance(value, dict):
            principals.extend(flatten_principals(value))
    return principals


class PolicyStatement(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    effect: str = Field(alias="Effect")
    principal: dict = Field(alias="Principal")
    action: str = Field(alias="Action")
    condition: dict = Field(alias="Condition")


class PolicyStatementOutput(PolicyStatement):
    entity_type: Literal["User", "Group", "Role"] = Field(alias="EntityType")
    entity_arn: str = Field(alias="EntityArn")
    policy: str


class InlinePolicy(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    entity_type: Literal["User", "Group", "Role"] = Field(alias="EntityType")
    entity_name: str = Field(alias="EntityName")
    entity_id: str = Field(alias="EntityId")
    entity_arn: str = Field(alias="EntityArn")
    policy_name: str = Field(alias="PolicyName")
    policy_document: dict = Field(alias="PolicyDocument")
    account_id: str = Field(alias="AccountId")


class Policy(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    policy_name: str = Field(alias="PolicyName")
    policy_id: str = Field(alias="PolicyId")
    arn: str = Field(alias="Arn")
    path: str = Field(alias="Path")
    default_version_id: str = Field(alias="DefaultVersionId")
    attachment_count: int = Field(alias="AttachmentCount")
    create_date: datetime = Field(alias="CreateDate")
    update_date: datetime | None = Field(alias="UpdateDate", default=None)
    account_id: str | None = Field(alias="AccountId", default=None)
    is_aws_managed: bool = Field(alias="IsAWSManaged")
    policy_document: dict = Field(alias="PolicyDocument")


class ExtendedPolicyProperties(NodeProperties):
    model_config = ConfigDict(extra="allow", populate_by_name=True)
    is_aws_managed: bool


class ExtendedInlinePolicyProperties(NodeProperties):
    model_config = ConfigDict(extra="allow", populate_by_name=True)
    source_entity: str
    source_entity_type: str


class GlobalPolicy(Node):
    _policy: InlinePolicy = PrivateAttr()
    _lookup: LookupManager = PrivateAttr()

    _ENTITY_NODE_TYPES = {
        "User": "AWSUser",
        "Group": "AWSGroup",
        "Role": "AWSRole",
    }

    def does_role_match(self, principals: list[str]) -> bool:
        for principal in principals:
            if f"{self._account_id}:root" in principal:
                return True
            elif fnmatch.fnmatch(principal, self._policy.entity_arn):
                return True
        return False

    def verify_roles(self, roles: list) -> list[Edge]:
        allowed_roles = []
        for role_arn, role_name, condition, principal in roles:
            match_principal = self.does_role_match(flatten_principals(principal))
            if match_principal:
                start_principal = EdgePath(value=self._principal_guid, match_by="id")
                role_id = gen_guid(
                    name=role_arn,
                    node_type=NodeTypes.AWSRole.value,
                    account_id=self.properties.aws_account_id,
                )
                end = EdgePath(value=role_id, match_by="id")
                principal_edge = Edge(
                    kind="AWSCanAssumeRole",
                    start=start_principal,
                    end=end,
                )
                # allowed_roles.append(edge)

                start_policy = EdgePath(value=self.id, match_by="id")
                policy_edge = Edge(kind="AWSAllowsAssume", start=start_policy, end=end)
                allowed_roles.append(policy_edge)

        return allowed_roles

    @property
    def _assume_roles(self) -> list[Edge]:
        allowed_roles = []
        for statement in self._policy.policy_document["Statement"]:
            if (
                statement["Action"] == "sts:AssumeRole"
                and statement["Effect"] == "Allow"
            ):
                get_roles = self._lookup.role_trusts(statement["Resource"])
                allowed_roles.extend(self.verify_roles(get_roles))

        return allowed_roles


class InlinePolicyNode(GlobalPolicy):
    properties: ExtendedInlinePolicyProperties

    @property
    def _principal_guid(self) -> str:
        node_type = self._ENTITY_NODE_TYPES[self.properties.source_entity_type]
        return gen_guid(
            name=self.properties.source_entity,
            node_type=node_type,
            account_id=self.properties.aws_account_id,
        )

    @property
    def _attaches_policy(self):
        start = EdgePath(value=self._principal_guid, match_by="id")
        end = EdgePath(value=self.id, match_by="id")
        return [
            Edge(
                kind="AWSAttachesPolicy",
                start=start,
                end=end,
            )
        ]

    @property
    def edges(self) -> list[Edge]:
        return [*self._attaches_policy, *self._assume_roles]

    @classmethod
    def from_input(cls, **kwargs) -> "InlinePolicyNode":
        model = InlinePolicy(**kwargs)
        properties = ExtendedInlinePolicyProperties(
            name=f"{model.entity_name}_{model.policy_name}",
            displayname=f"{model.entity_name}_{model.policy_name}",
            aws_account_id=model.account_id,
            aws_region="global",
            source_entity=model.entity_arn,
            source_entity_type=model.entity_type,
        )
        node = cls(kinds=[NodeTypes.AWSInlinePolicy.value], properties=properties)
        node.attach_context(model.account_id)
        node._policy = model
        return node


class PolicyNode(GlobalPolicy):
    properties: NodeProperties

    @property
    def edges(self):
        # for statement in self._policy.policy_document["Statement"]:
        #     if (
        #         statement["Action"] == "sts:AssumeRole"
        #         and statement["Effect"] == "Allow"
        #     ):
        #         print(statement)
        # # print
        # # print(self._policy.policy_document)
        return []

    @classmethod
    def from_input(cls, **kwargs) -> "PolicyNode":
        model = Policy(**kwargs)
        properties = ExtendedPolicyProperties(
            name=model.policy_name,
            displayname=model.policy_name,
            aws_account_id=model.account_id,
            aws_region="global",
            arn=model.arn,
            created_at=model.create_date,
            is_aws_managed=model.is_aws_managed,
        )
        node = cls(kinds=[NodeTypes.AWSPolicy.value], properties=properties)
        node.attach_context(model.account_id)
        node._policy = model
        return node


class PolicyAttachment(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)
    policy_arn: str = Field(alias="PolicyArn")
    entity_type: Literal["User", "Group", "Role"] = Field(alias="EntityType")
    entity_name: str = Field(alias="EntityName")
    entity_id: str = Field(alias="EntityId")
    entity_arn: str | None = Field(alias="EntityArn", default=None)
    account_id: str | None = Field(alias="AccountId", default=None)
    policy_document: dict = Field(alias="PolicyDocument")


class PolicyAttachmentEdges(BaseModel):
    policy: PolicyAttachment
    _lookup: LookupManager = PrivateAttr()

    _ENTITY_NODE_TYPES = {
        "User": "AWSUser",
        "Group": "AWSGroup",
        "Role": "AWSRole",
    }

    @property
    def _policy_guid(self) -> str:
        return gen_guid(
            name=self.policy.policy_arn,
            node_type=NodeTypes.AWSPolicy.value,
            account_id=self.policy.account_id,
        )

    @property
    def _principal_guid(self) -> str:
        lookup_arn = {
            "User": self._lookup.user,
            "Group": self._lookup.group,
            "Role": self._lookup.role,
        }
        node_type = self._ENTITY_NODE_TYPES[self.policy.entity_type]
        source_key = lookup_arn[self.policy.entity_type](self.policy.entity_name)
        return gen_guid(
            name=source_key,
            node_type=node_type,
            account_id=self.policy.account_id,
        )

    @property
    def edges(self) -> list[Edge]:
        start = EdgePath(value=self._principal_guid, match_by="id")
        end = EdgePath(value=self._policy_guid, match_by="id")
        properties = EdgeProperties(entity_type=self.policy.entity_type)
        return [
            Edge(kind="AWSAttachesPolicy", start=start, end=end, properties=properties)
        ]

    @classmethod
    def from_input(cls, **kwargs) -> "PolicyAttachmentEdges":
        model = PolicyAttachment(**kwargs)
        return cls(policy=model)

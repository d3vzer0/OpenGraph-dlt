from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr

from ..entries import Edge, EdgePath, EdgeProperties, NodeProperties, Node
from sources.aws.utils.guid import NodeTypes, gen_guid
from sources.aws.utils.lookup import LookupManager


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


class InlinePolicyNode(Node):
    properties: ExtendedInlinePolicyProperties

    _ENTITY_NODE_TYPES = {
        "User": "AWSUser",
        "Group": "AWSGroup",
        "Role": "AWSRole",
    }

    @property
    def _principal_guid(self) -> str:
        node_type = self._ENTITY_NODE_TYPES[self.properties.source_entity_type]
        return gen_guid(
            name=self.properties.source_entity,
            node_type=node_type,
            account_id=self.properties.aws_account_id,
        )

    @property
    def edges(self):
        start = EdgePath(value=self._principal_guid, match_by="id")
        end = EdgePath(value=self.id, match_by="id")
        return [
            Edge(
                kind="AWSAttachesInlinePolicy",
                start=start,
                end=end,
            )
        ]

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
        return node


class PolicyNode(Node):
    properties: NodeProperties

    @property
    def edges(self):
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

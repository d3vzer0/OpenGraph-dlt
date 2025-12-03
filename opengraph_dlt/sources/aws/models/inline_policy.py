from typing import Literal
from pydantic import ConfigDict, Field
from opengraph_dlt.sources.aws.models.graph import (
    NodeProperties,
    Node,
    NodeTypes,
    AWSCollector,
    BaseResource,
)
from opengraph_dlt.sources.shared.models.entries import Edge, EdgePath
from opengraph_dlt.sources.shared.docs import graph_resource, EdgeDef, NodeDef
import fnmatch

ENTITY_NODE_TYPES = {
    "User": NodeTypes.AWSUser.value,
    "Group": NodeTypes.AWSGroup.value,
    "Role": NodeTypes.AWSRole.value,
}


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


class ExtendedInlinePolicyProperties(NodeProperties):
    model_config = ConfigDict(extra="allow", populate_by_name=True)
    source_entity: str
    source_entity_type: str


class InlinePolicyNode(Node):
    properties: ExtendedInlinePolicyProperties


@graph_resource(
    node=NodeDef(
        kind=NodeTypes.AWSInlinePolicy.value,
        description="AWS Inline policy as individual node",
    ),
    edges=[
        EdgeDef(
            start=NodeTypes.AWSUser.value,
            end=NodeTypes.AWSInlinePolicy.value,
            kind="AWSAttachesPolicy",
            description="IAM user uses inline policy",
        ),
        EdgeDef(
            start=NodeTypes.AWSGroup.value,
            end=NodeTypes.AWSInlinePolicy.value,
            kind="AWSAttachesPolicy",
            description="IAM group uses inline policy",
        ),
        EdgeDef(
            start=NodeTypes.AWSRole.value,
            end=NodeTypes.AWSInlinePolicy.value,
            kind="AWSAttachesPolicy",
            description="IAM role uses inline policy",
        ),
    ],
)
class InlinePolicy(BaseResource):
    model_config = ConfigDict(populate_by_name=True)

    entity_type: Literal["User", "Group", "Role"] = Field(alias="EntityType")
    entity_name: str = Field(alias="EntityName")
    entity_id: str = Field(alias="EntityId")
    entity_arn: str = Field(alias="EntityArn")
    policy_name: str = Field(alias="PolicyName")
    policy_document: dict = Field(alias="PolicyDocument")
    account_id: str = Field(alias="AccountId")

    def does_role_match(self, principals: list[str]) -> bool:
        for principal in principals:
            if f"{self.account_id}:root" in principal:
                return True
            elif fnmatch.fnmatch(principal, self.entity_arn):
                return True
        return False

    def verify_roles(self, roles: list) -> list[Edge]:
        allowed_roles = []
        for role_arn, role_name, condition, principal in roles:
            match_principal = self.does_role_match(flatten_principals(principal))
            if match_principal:
                role_id = AWSCollector.guid(
                    name=role_arn,
                    node_type=NodeTypes.AWSRole,
                    account_id=self.account_id,
                )
                end = EdgePath(value=role_id, match_by="id")
                start_policy = EdgePath(value=self.as_node.id, match_by="id")
                policy_edge = Edge(kind="AWSAllowsAssume", start=start_policy, end=end)
                allowed_roles.append(policy_edge)

        return allowed_roles

    @property
    def _assume_roles(self) -> list[Edge]:
        allowed_roles = []
        for statement in self.policy_document["Statement"]:
            if (
                statement["Action"] == "sts:AssumeRole"
                and statement["Effect"] == "Allow"
            ):
                get_roles = self._lookup.role_trusts(statement["Resource"])
                allowed_roles.extend(self.verify_roles(get_roles))

        return allowed_roles

    @property
    def _principal_guid(self) -> str:
        node_type = ENTITY_NODE_TYPES[self.entity_type]
        return AWSCollector.guid(
            name=self.entity_arn,
            node_type=node_type,
            account_id=self.account_id,
        )

    @property
    def _attaches_policy(self):
        start = EdgePath(value=self._principal_guid, match_by="id")
        end = EdgePath(value=self.as_node.id, match_by="id")
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

    @property
    def as_node(self) -> "InlinePolicyNode":
        properties = ExtendedInlinePolicyProperties(
            name=f"{self.entity_name}_{self.policy_name}",
            displayname=f"{self.entity_name}_{self.policy_name}",
            aws_account_id=self.account_id,
            aws_region="global",
            source_entity=self.entity_arn,
            source_entity_type=self.entity_type,
        )
        node = InlinePolicyNode(
            kinds=[NodeTypes.AWSInlinePolicy.value], properties=properties
        )
        node.attach_context(self.account_id)
        return node

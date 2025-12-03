from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from opengraph_dlt.sources.aws.models.graph import Node, NodeProperties, NodeTypes, Edge
from opengraph_dlt.sources.shared.docs import graph_resource, NodeDef


class RoleProperties(NodeProperties):
    model_config = ConfigDict(extra="allow")
    role_id: str
    path: str
    assume_role_policy: Optional[dict] = None


class RoleNode(Node):
    properties: RoleProperties


@graph_resource(
    node=NodeDef(kind=NodeTypes.AWSRole.value, description="Example description")
)
class Role(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    role_name: str = Field(alias="RoleName")
    role_id: str = Field(alias="RoleId")
    arn: str = Field(alias="Arn")
    path: str = Field(alias="Path")
    create_date: datetime = Field(alias="CreateDate")
    assume_role_policy_document: Optional[dict] = Field(
        alias="AssumeRolePolicyDocument", default=None
    )
    description: Optional[str] = Field(alias="Description", default=None)
    account_id: Optional[str] = Field(alias="AccountId", default=None)

    @property
    def as_node(self) -> "RoleNode":
        properties = RoleProperties(
            name=self.role_name,
            displayname=self.role_name,
            aws_account_id=self.account_id,
            role_id=self.role_id,
            aws_region="global",
            arn=self.arn,
            path=self.path,
            assume_role_policy=self.assume_role_policy_document,
            description=self.description,
            created_at=self.create_date,
        )
        node = RoleNode(kinds=[NodeTypes.AWSRole.value], properties=properties)
        node.attach_context(self.account_id)
        return node

    @property
    def edges(self) -> list[Edge]:
        return []

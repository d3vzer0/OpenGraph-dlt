from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from opengraph_dlt.sources.aws.models.graph import Node, NodeProperties, NodeTypes, Edge
from opengraph_dlt.sources.shared.docs import graph_resource, NodeDef


class GroupProperties(NodeProperties):
    model_config = ConfigDict(extra="allow")
    group_id: str
    path: str


class GroupNode(Node):
    properties: GroupProperties

    @property
    def edges(self):
        return []


@graph_resource(
    node=NodeDef(kind=NodeTypes.AWSGroup.value, description="AWS Group node")
)
class Group(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    group_name: str = Field(alias="GroupName")
    group_id: str = Field(alias="GroupId")
    arn: str = Field(alias="Arn")
    path: str = Field(alias="Path")
    create_date: datetime = Field(alias="CreateDate")
    account_id: Optional[str] = Field(alias="AccountId", default=None)

    @property
    def as_node(self) -> "GroupNode":
        properties = GroupProperties(
            name=self.group_name,
            displayname=self.group_name,
            aws_account_id=self.account_id,
            aws_region="global",
            group_id=self.group_id,
            arn=self.arn,
            path=self.path,
            created_at=self.create_date,
        )
        node = GroupNode(kinds=[NodeTypes.AWSGroup.value], properties=properties)
        node.attach_context(self.account_id)
        return node

    @property
    def edges(self) -> list[Edge]:
        return []

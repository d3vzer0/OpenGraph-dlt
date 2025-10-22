from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from sources.aws.utils.guid import NodeTypes
from sources.aws.models.graph import Node, NodeProperties


class Group(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    group_name: str = Field(alias="GroupName")
    group_id: str = Field(alias="GroupId")
    arn: str = Field(alias="Arn")
    path: str = Field(alias="Path")
    create_date: datetime = Field(alias="CreateDate")
    account_id: Optional[str] = Field(alias="AccountId", default=None)


class GroupProperties(NodeProperties):
    model_config = ConfigDict(extra="allow")
    group_id: str
    path: str


class GroupNode(Node):
    properties: GroupProperties

    @property
    def edges(self):
        return []

    @classmethod
    def from_input(cls, **kwargs) -> "GroupNode":
        model = Group(**kwargs)
        properties = GroupProperties(
            name=model.group_name,
            displayname=model.group_name,
            aws_account_id=model.account_id,
            aws_region="global",
            group_id=model.group_id,
            arn=model.arn,
            path=model.path,
            created_at=model.create_date,
        )
        node = cls(kinds=[NodeTypes.AWSGroup.value], properties=properties)
        node.attach_context(model.account_id)
        return node

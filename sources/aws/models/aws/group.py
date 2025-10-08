from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from sources.aws.utils.guid import NodeTypes
from ..entries import Node, NodeProperties


class Group(BaseModel):
    model_config = ConfigDict(extra="allow")

    GroupName: str
    GroupId: str
    Arn: str
    Path: str
    CreateDate: datetime
    AccountId: Optional[str] = None


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
            name=model.GroupName,
            displayname=model.GroupName,
            aws_account_id=model.AccountId,
            group_id=model.GroupId,
            arn=model.Arn,
            path=model.Path,
            created_at=model.CreateDate,
        )
        node = cls(kinds=[NodeTypes.AWSGroup.value], properties=properties)
        node.attach_context(model.AccountId)
        return node

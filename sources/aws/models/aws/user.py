from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from sources.aws.utils.guid import NodeTypes
from ..entries import Node, NodeProperties


class User(BaseModel):
    model_config = ConfigDict(extra="allow")

    UserName: str
    UserId: str
    Arn: str
    Path: str
    CreateDate: datetime
    PasswordLastUsed: Optional[datetime] = None
    AccountId: Optional[str] = None


class UserProperties(NodeProperties):
    model_config = ConfigDict(extra="allow")
    user_id: str
    path: str
    password_last_used: Optional[datetime] = None


class UserNode(Node):
    properties: UserProperties

    @property
    def edges(self):
        return []

    @classmethod
    def from_input(cls, **kwargs) -> "UserNode":
        model = User(**kwargs)
        properties = UserProperties(
            name=model.UserName,
            displayname=model.UserName,
            aws_account_id=model.AccountId,
            user_id=model.UserId,
            arn=model.Arn,
            path=model.Path,
            password_last_used=model.PasswordLastUsed,
            created_at=model.CreateDate,
        )
        node = cls(kinds=[NodeTypes.AWSUser.value], properties=properties)
        node.attach_context(model.AccountId)
        return node

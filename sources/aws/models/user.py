from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from sources.aws.utils.guid import NodeTypes
from sources.aws.models.graph import Node, NodeProperties


class User(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    user_name: str = Field(alias="UserName")
    user_id: str = Field(alias="UserId")
    arn: str = Field(alias="Arn")
    path: str = Field(alias="Path")
    create_date: datetime = Field(alias="CreateDate")
    password_last_used: Optional[datetime] = Field(
        alias="PasswordLastUsed", default=None
    )
    account_id: Optional[str] = Field(alias="AccountId", default=None)


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
            name=model.user_name,
            displayname=model.user_name,
            aws_account_id=model.account_id,
            aws_region="global",
            user_id=model.user_id,
            arn=model.arn,
            path=model.path,
            password_last_used=model.password_last_used,
            created_at=model.create_date,
        )
        node = cls(kinds=[NodeTypes.AWSUser.value], properties=properties)
        node.attach_context(model.account_id)
        return node

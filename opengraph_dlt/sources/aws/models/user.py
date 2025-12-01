from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from opengraph_dlt.sources.aws.models.graph import Node, NodeProperties, NodeTypes, Edge


class UserProperties(NodeProperties):
    model_config = ConfigDict(extra="allow")
    user_id: str
    path: str
    password_last_used: Optional[datetime] = None


class UserNode(Node):
    properties: UserProperties


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

    @property
    def as_node(self) -> "UserNode":
        properties = UserProperties(
            name=self.user_name,
            displayname=self.user_name,
            aws_account_id=self.account_id,
            aws_region="global",
            user_id=self.user_id,
            arn=self.arn,
            path=self.path,
            password_last_used=self.password_last_used,
            created_at=self.create_date,
        )
        node = UserNode(kinds=[NodeTypes.AWSUser.value], properties=properties)
        node.attach_context(self.account_id)
        return node

    @property
    def edges(self) -> list[Edge]:
        return []

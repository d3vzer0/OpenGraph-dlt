from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from sources.aws.utils.guid import NodeTypes
from ..entries import Node, NodeProperties


class Role(BaseModel):
    model_config = ConfigDict(extra="allow")

    RoleName: str
    RoleId: str
    Arn: str
    Path: str
    CreateDate: datetime
    AssumeRolePolicyDocument: Optional[dict] = None
    Description: Optional[str] = None
    AccountId: Optional[str] = None


class RoleProperties(NodeProperties):
    model_config = ConfigDict(extra="allow")
    role_id: str
    path: str
    assume_role_policy: Optional[dict] = None


class RoleNode(Node):
    properties: RoleProperties

    @property
    def edges(self):
        return []

    @classmethod
    def from_input(cls, **kwargs) -> "RoleNode":
        model = Role(**kwargs)
        properties = RoleProperties(
            name=model.RoleName,
            displayname=model.RoleName,
            aws_account_id=model.AccountId,
            role_id=model.RoleId,
            arn=model.Arn,
            path=model.Path,
            assume_role_policy=model.AssumeRolePolicyDocument,
            description=model.Description,
            created_at=model.CreateDate,
        )
        node = cls(kinds=[NodeTypes.AWSRole.value], properties=properties)
        node.attach_context(model.AccountId)
        return node

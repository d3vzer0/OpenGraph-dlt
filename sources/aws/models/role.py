from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from sources.aws.models.graph import Node, NodeProperties, NodeTypes


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


class RoleProperties(NodeProperties):
    model_config = ConfigDict(extra="allow")
    role_id: str
    path: str
    assume_role_policy: Optional[dict] = None


class RoleNode(Node):
    properties: RoleProperties

    # @property
    # def _assume_role(self):
    #     identities_allowed = []
    #     for statement in self.properties.assume_role_policy["Statement"]:

    @property
    def edges(self):
        return []

    @classmethod
    def from_input(cls, **kwargs) -> "RoleNode":
        model = Role(**kwargs)
        properties = RoleProperties(
            name=model.role_name,
            displayname=model.role_name,
            aws_account_id=model.account_id,
            role_id=model.role_id,
            aws_region="global",
            arn=model.arn,
            path=model.path,
            assume_role_policy=model.assume_role_policy_document,
            description=model.description,
            created_at=model.create_date,
        )
        node = cls(kinds=[NodeTypes.AWSRole.value], properties=properties)
        node.attach_context(model.account_id)
        return node

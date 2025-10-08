from pydantic import BaseModel, ConfigDict, computed_field
from sources.aws.utils.guid import NodeTypes
from ..entries import Node, NodeProperties
from datetime import datetime


class PropertiesData(BaseModel):
    Key: str
    Value: str


class ResourceProperties(BaseModel):
    Name: str
    LastReportedAt: datetime
    Data: list[PropertiesData]


class Resource(BaseModel):
    model_config = ConfigDict(extra="allow")
    Arn: str
    OwningAccountId: str
    Region: str
    ResourceType: str
    Service: str
    Properties: list[ResourceProperties]

    @computed_field
    @property
    def name(self) -> str:
        return self.Arn.split(":")[-1]


class ExtendedProperties(NodeProperties):
    model_config = ConfigDict(extra="allow")


# class ResourceNode(Node):
#     properties: ResourceProperties

#     @property
#     def edges(self):
#         return []

#     @classmethod
#     def from_input(cls, **kwargs) -> "UserNode":
#         model = Resource(**kwargs)
#         properties = ResourceProperties(
#             name=model.UserName,
#             displayname=model.UserName,
#             aws_account_id=model.AccountId,
#             arn=model.Arn,
#         )
#         node = cls(kinds=[NodeTypes.AWSUser.value], properties=properties)
#         node.attach_context(model.AccountId)
#         return node

from pydantic import BaseModel, ConfigDict, computed_field, Field
from sources.aws.utils.guid import NodeTypes, gen_node_type
from sources.aws.models.graph import Node, NodeProperties
from datetime import datetime
from enum import Enum


class PropertiesData(BaseModel):
    key: str = Field(alias="Key")
    value: str = Field(alias="Value")


class ResourceProperties(BaseModel):
    name: str = Field(alias="Name")
    last_reported_at: datetime = Field(alias="LastReportedAt")
    data: list[PropertiesData] = Field(alias="Data")


class Resource(BaseModel):
    model_config = ConfigDict(extra="allow")
    arn: str = Field(alias="Arn")
    owning_account_id: str = Field(alias="OwningAccountId")
    region: str = Field(alias="Region")
    resource_type: str = Field(alias="ResourceType")
    service: str = Field(alias="Service")
    properties: list[ResourceProperties] = Field(alias="Properties")

    @computed_field
    @property
    def name(self) -> str:
        return self.arn.split(":")[-1]


class ExtendedProperties(NodeProperties):
    model_config = ConfigDict(extra="allow")


class ResourceNode(Node):
    properties: ExtendedProperties

    @property
    def edges(self):
        return []

    @classmethod
    def from_input(cls, **kwargs) -> "ResourceNode":
        model = Resource(**kwargs)
        node_properties = ExtendedProperties(
            name=model.name,
            displayname=model.name,
            aws_account_id=model.owning_account_id,
            aws_region=model.region,
            arn=model.arn,
        )

        kind = gen_node_type(model.resource_type)
        node = cls(kinds=[kind, "BaseAWS"], properties=node_properties)
        node.attach_context(model.owning_account_id)
        return node

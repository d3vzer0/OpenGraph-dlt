from collections.abc import Iterator
from pydantic import BaseModel, ConfigDict, computed_field, Field
from opengraph_dlt.sources.aws.models.graph import (
    Node,
    NodeProperties,
    NodeTypes,
    AWSCollector,
    Edge,
)
from opengraph_dlt.sources.shared.docs import graph_resource, NodeDef

from datetime import datetime


class ExtendedProperties(NodeProperties):
    model_config = ConfigDict(extra="allow")


class ResourceNode(Node):
    properties: ExtendedProperties


class PropertiesData(BaseModel):
    key: str = Field(alias="Key")
    value: str = Field(alias="Value")


class ResourceProperties(BaseModel):
    name: str = Field(alias="Name")
    last_reported_at: datetime = Field(alias="LastReportedAt")
    data: list[PropertiesData] = Field(alias="Data")


@graph_resource(
    node=NodeDef(kind="AWSResource", description="AWS dynamic resource node")
)
class Resource(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)
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

    @property
    def edges(self) -> Iterator[Edge]:
        yield from ()

    @property
    def as_node(self) -> "ResourceNode":
        node_properties = ExtendedProperties(
            name=self.name,
            displayname=self.name,
            aws_account_id=self.owning_account_id,
            aws_region=self.region,
            arn=self.arn,
        )

        kind = AWSCollector.gen_node_type(self.resource_type)
        node = ResourceNode(kinds=[kind, "BaseAWS"], properties=node_properties)
        node.attach_context(self.owning_account_id)
        return node

from pydantic import BaseModel, ConfigDict, Field, computed_field
from opengraph_dlt.sources.shared.models.graph import MetaData, Graph as CommonGraph
from opengraph_dlt.sources.shared.models.entries import Node as BaseNode, Edge
from opengraph_dlt.sources.shared.guid import Collector
import uuid


class DummyCollector(Collector):

    @staticmethod
    def guid(
        name: str,
        resource_type: str,
    ):
        uuid_namespace = uuid.NAMESPACE_DNS
        resource_path = f"{name}.{resource_type}"
        return str(uuid.uuid5(uuid_namespace, resource_path))


class BaseResource(BaseModel): ...


class NodeProperties(BaseModel):
    model_config = ConfigDict(extra="allow")
    name: str
    displayname: str


class Node(BaseNode):
    properties: NodeProperties

    @computed_field
    @property
    def id(self) -> str:
        kind = self.kinds[0]
        dyn_uid = DummyCollector.guid(self.properties.name, kind)
        return dyn_uid


class GraphEntries(BaseModel):
    nodes: list[Node] = []
    edges: list[Edge] = Field(default_factory=list)


class Graph(CommonGraph):
    graph: GraphEntries
    metadata: MetaData = Field(default_factory=MetaData)

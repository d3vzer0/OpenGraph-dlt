from pydantic import BaseModel, Field, PrivateAttr, computed_field
from opengraph_dlt.sources.shared.models.graph import MetaData, Graph as CommonGraph
from opengraph_dlt.sources.shared.guid import Collector
from abc import ABC
from typing import Optional
from opengraph_dlt.sources.shared.models.entries import (
    Node as BaseNode,
    Edge,
)
from enum import Enum
import uuid


class NodeTypes(str, Enum):
    R7Vulnerability = "R7Vulnerability"


class R7Collector(Collector):
    name: str = "DLTRapid7"

    @staticmethod
    def guid(
        name: str,
        node_type: NodeTypes | str,
        scope: Optional[str] = "global",
    ):
        type_value = node_type.value if isinstance(node_type, NodeTypes) else node_type
        uuid_namespace = uuid.NAMESPACE_DNS
        resource_path = f"{name}.{type_value}.{scope}.{scope}"
        return str(uuid.uuid5(uuid_namespace, resource_path))


class Node(BaseNode, ABC):
    _scope: Optional[str] = PrivateAttr(default=None)

    @computed_field
    @property
    def id(self) -> str:
        return R7Collector.guid(
            self.properties.name,
            self.kinds[0],
        )


class GraphEntries(BaseModel):
    nodes: list[Node] = []
    edges: list[Edge] = Field(default_factory=list)


class Graph(CommonGraph):
    graph: GraphEntries
    metadata: MetaData = Field(default_factory=MetaData)

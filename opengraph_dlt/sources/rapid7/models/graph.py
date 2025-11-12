from pydantic import BaseModel, Field, PrivateAttr, computed_field
from opengraph_dlt.sources.shared.models.graph import MetaData, Graph as CommonGraph
from abc import ABC
from typing import Optional
from opengraph_dlt.sources.shared.models.entries import (
    Node as BaseNode,
    Edge,
)
from enum import Enum
from typing import Optional
import uuid


class NodeTypes(str, Enum):
    R7Vulnerability = "R7Vulnerability"


def gen_guid(
    name: str, node_type: str, scope: Optional[str] = "global", collector: str = "r7"
) -> str:
    uuid_namespace = uuid.NAMESPACE_DNS
    resource_path = f"{name}.{node_type}.{scope}.{collector}"
    return str(uuid.uuid5(uuid_namespace, resource_path))


class Node(BaseNode, ABC):
    _scope: Optional[str] = PrivateAttr(default=None)

    @computed_field
    @property
    def id(self) -> str:
        return gen_guid(
            self.properties.name,
            self.kinds[0],
        )


class GraphEntries(BaseModel):
    nodes: list[Node] = []
    edges: list[Edge] = Field(default_factory=list)


class Graph(CommonGraph):
    graph: GraphEntries
    metadata: MetaData = Field(default_factory=MetaData)

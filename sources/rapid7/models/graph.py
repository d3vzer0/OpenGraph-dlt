from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, computed_field
from typing import Union
from sources.shared.models.graph import MetaData, Graph as CommonGraph
from abc import ABC
from datetime import datetime
from typing import Optional
from sources.rapid7.utils.guid import gen_guid
from sources.shared.models.entries import (
    Node as BaseNode,
    Edge,
)


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

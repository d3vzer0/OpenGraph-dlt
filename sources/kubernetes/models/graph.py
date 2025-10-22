from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, computed_field
from sources.shared.models.graph import MetaData, Graph as CommonGraph
from abc import ABC
from datetime import datetime
from typing import Optional
from sources.kubernetes.utils.guid import get_guid, NodeTypes, get_generic_guid
from sources.kubernetes.utils.lookup import LookupManager
from sources.shared.models.entries import Node as BaseNode, Edge


class NodeProperties(BaseModel):
    model_config = ConfigDict(extra="allow")
    name: str
    displayname: str
    namespace: str | None
    last_seen: datetime = Field(default_factory=datetime.now)
    uid: str | None


class Node(BaseNode, ABC):
    properties: NodeProperties

    _lookup: LookupManager = PrivateAttr()
    _cluster: str = PrivateAttr()
    _scope: Optional[str] = PrivateAttr(default=None)

    @computed_field
    @property
    def id(self) -> str:
        scope = (
            "__global__" if not self.properties.namespace else self.properties.namespace
        )
        if self.kinds[0] in NodeTypes:
            dyn_uid = get_guid(
                self.properties.name, NodeTypes[self.kinds[0]], self._cluster, scope
            )
        else:
            dyn_uid = get_generic_guid(
                self.properties.name, self.kinds[0], self._cluster, scope
            )
        return dyn_uid


class GraphEntries(BaseModel):
    nodes: list[Node] = []
    edges: list[Edge] = Field(default_factory=list)


class Graph(CommonGraph):
    graph: GraphEntries
    metadata: MetaData = Field(default_factory=MetaData)

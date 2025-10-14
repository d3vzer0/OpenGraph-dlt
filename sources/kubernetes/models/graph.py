from .entries import Node, Edge

from .k8s.pod import PodNode
from .k8s.role import RoleNode
from .k8s.cluster_role import ClusterRoleNode
from .k8s.resource import ResourceNode
from pydantic import BaseModel, ConfigDict, Field
from typing import Union


class GraphEntries(BaseModel):
    nodes: list[Union[Node, PodNode, RoleNode, ClusterRoleNode, ResourceNode]] = []
    edges: list[Edge] = []


class CollectorProperties(BaseModel):
    model_config = ConfigDict(extra="allow")
    collection_methods: list[str] = ["Custom Method"]
    windows_server_version: str = "n/a"


class MetaDataCollector(BaseModel):
    name: str = "opengraph-dlt-k8s"
    version: str = "0.0.3"
    properties: CollectorProperties = Field(default_factory=CollectorProperties)


class MetaData(BaseModel):
    ingest_version: str = "v1"
    collector: MetaDataCollector = Field(default_factory=MetaDataCollector)


class Graph(BaseModel):
    graph: GraphEntries
    metadata: MetaData = Field(default_factory=MetaData)

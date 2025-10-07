from .entries import Node, Edge
from pydantic import BaseModel, ConfigDict, Field


class GraphEntries(BaseModel):
    nodes: list[Node] = []
    edges: list[Edge] = []


class CollectorProperties(BaseModel):
    model_config = ConfigDict(extra="allow")
    collection_methods: list[str] = ["Custom Method"]
    windows_server_version: str = "n/a"


class MetaDataCollector(BaseModel):
    name: str = "OpenGraph-nlt"
    version: str = "beta"
    properties: CollectorProperties = Field(default_factory=CollectorProperties)


class MetaData(BaseModel):
    ingest_version: str = "v1"
    collector: MetaDataCollector = Field(default_factory=MetaDataCollector)


class Graph(BaseModel):
    graph: GraphEntries
    metadata: MetaData = Field(default_factory=MetaData)

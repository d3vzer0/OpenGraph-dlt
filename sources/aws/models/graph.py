from pydantic import BaseModel, ConfigDict, Field

from .entries import Edge, Node


class GraphEntries(BaseModel):
    nodes: list[Node] = Field(default_factory=list)
    edges: list[Edge] = Field(default_factory=list)


class CollectorProperties(BaseModel):
    model_config = ConfigDict(extra="allow")
    collection_methods: list[str] = ["dlt"]
    windows_server_version: str = "n/a"


class MetaDataCollector(BaseModel):
    name: str = "opengraph-dlt-aws"
    version: str = "0.1.0"
    properties: CollectorProperties = Field(default_factory=CollectorProperties)


class MetaData(BaseModel):
    ingest_version: str = "v1"
    collector: MetaDataCollector = Field(default_factory=MetaDataCollector)


class Graph(BaseModel):
    graph: GraphEntries
    metadata: MetaData = Field(default_factory=MetaData)

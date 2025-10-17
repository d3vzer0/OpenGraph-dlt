from pydantic import BaseModel, ConfigDict, Field
from typing import Union
from .entries import Node, Edge
from .r7.vulnerability import VulnerabilityNode


class GraphEntries(BaseModel):
    nodes: list[Union[Node, VulnerabilityNode]] = []
    edges: list[Edge] = Field(default_factory=list)


class CollectorProperties(BaseModel):
    model_config = ConfigDict(extra="allow")
    collection_methods: list[str] = ["dlt"]
    windows_server_version: str = "n/a"


class MetaDataCollector(BaseModel):
    name: str = "opengraph-dlt-rapid7"
    version: str = "0.0.1"
    properties: CollectorProperties = Field(default_factory=CollectorProperties)


class MetaData(BaseModel):
    ingest_version: str = "v1"
    collector: MetaDataCollector = Field(default_factory=MetaDataCollector)


class Graph(BaseModel):
    graph: GraphEntries
    metadata: MetaData = Field(default_factory=MetaData)

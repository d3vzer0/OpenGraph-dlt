from pydantic import BaseModel, ConfigDict


class NodeProperties(BaseModel):
    model_config = ConfigDict(extra="allow")
    name: str
    displayname: str


class Node(BaseModel):
    id: str
    kinds: list[str]
    properties: NodeProperties


class EdgePath(BaseModel):
    value: str
    match_by: str


class EdgeProperties(BaseModel):
    model_config = ConfigDict(extra="allow")
    composed: bool = False


class Edge(BaseModel):
    kind: str
    start: EdgePath
    end: EdgePath
    properties: EdgeProperties

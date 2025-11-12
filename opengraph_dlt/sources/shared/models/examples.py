from pydantic import BaseModel, Field
from typing import Optional


class ExampleEdge(BaseModel):
    kind: str
    target_kind: str
    source_kind: Optional[str] = None
    description: Optional[str] = None


class NodeExample(BaseModel):
    kind: str
    label: Optional[str] = None
    description: Optional[str] = None
    edges: list[ExampleEdge] = Field(default_factory=list)

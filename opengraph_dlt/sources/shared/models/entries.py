from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    PrivateAttr,
    computed_field,
)


class NodeProperties(BaseModel):
    model_config = ConfigDict(extra="allow")
    name: str
    displayname: str
    last_seen: datetime = Field(default_factory=datetime.utcnow)


class Node(BaseModel, ABC):
    model_config = ConfigDict(extra="allow")
    kinds: list[str]
    properties: NodeProperties
    _scope: Optional[str] = PrivateAttr(default=None)

    @computed_field
    @property
    @abstractmethod
    def id(self) -> str: ...  # noqa: E704

    # @classmethod
    # @abstractmethod
    # def from_input(cls, **kwargs) -> "Node": ...  # noqa: E704

    # @property
    # @abstractmethod
    # def edges(self) -> list["Edge"]: ...  # noqa: E704


class EdgePath(BaseModel):
    value: str
    match_by: str


class EdgeProperties(BaseModel):
    model_config = ConfigDict(extra="allow")
    composed: bool = False
    traversable: bool = False


class Edge(BaseModel):
    kind: str
    start: EdgePath
    end: EdgePath
    properties: EdgeProperties = Field(default_factory=EdgeProperties)

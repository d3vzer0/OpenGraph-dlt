from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, computed_field
from sources.rapid7.utils.guid import NodeTypes, gen_guid


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
    def id(self) -> str:
        return gen_guid(
            self.properties.name,
            self.kinds[0],
        )

    @classmethod
    @abstractmethod
    def from_input(cls, **kwargs) -> "Node": ...

    @property
    @abstractmethod
    def edges(self) -> list["Edge"]: ...

    def attach_context(
        self, account_id: Optional[str], scope: Optional[str] = None
    ) -> None:
        self._account_id = account_id
        self._scope = scope


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
    properties: EdgeProperties = Field(default_factory=EdgeProperties)

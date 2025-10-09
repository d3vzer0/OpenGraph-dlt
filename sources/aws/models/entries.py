from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, computed_field
from sources.aws.utils.guid import NodeTypes, gen_guid
from sources.aws.utils.lookup import LookupManager


class NodeProperties(BaseModel):
    model_config = ConfigDict(extra="allow")
    name: str
    displayname: str
    arn: Optional[str] = None
    aws_account_id: str
    aws_region: str
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    last_seen: datetime = Field(default_factory=datetime.utcnow)


class Node(BaseModel, ABC):
    model_config = ConfigDict(extra="allow")
    kinds: list[str]
    properties: NodeProperties

    _account_id: Optional[str] = PrivateAttr(default=None)
    _scope: Optional[str] = PrivateAttr(default=None)

    @computed_field
    def id(self) -> str:
        account = self.properties.aws_account_id or self._account_id
        name = self.properties.arn if self.properties.arn else self.properties.name
        return gen_guid(
            name, self.kinds[0], account_id=account, scope=self.properties.aws_region
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

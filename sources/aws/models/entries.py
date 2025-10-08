from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, computed_field
from sources.aws.utils.guid import NodeTypes, get_guid


class NodeProperties(BaseModel):
    model_config = ConfigDict(extra="allow")
    name: str
    displayname: str
    arn: Optional[str] = None
    aws_account_id: Optional[str] = None
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
        primary_kind = (
            self.kinds[0] if self.kinds else NodeTypes.AWSIdentityProvider.value
        )
        node_type = NodeTypes(primary_kind)
        account = self.properties.aws_account_id or self._account_id
        return get_guid(
            self.properties.name, node_type, account_id=account, scope=self._scope
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

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, computed_field
from sources.shared.models.graph import MetaData, Graph as CommonGraph
from abc import ABC
from datetime import datetime
from typing import Optional
from sources.aws.utils.guid import gen_guid
from sources.shared.models.entries import Node as BaseNode, Edge


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


class Node(BaseNode, ABC):
    properties: NodeProperties
    _account_id: Optional[str] = PrivateAttr(default=None)
    _scope: Optional[str] = PrivateAttr(default=None)

    @computed_field
    @property
    def id(self) -> str:
        account = self.properties.aws_account_id or self._account_id
        name = self.properties.arn if self.properties.arn else self.properties.name
        return gen_guid(
            name, self.kinds[0], account_id=account, scope=self.properties.aws_region
        )

    def attach_context(
        self, account_id: Optional[str], scope: Optional[str] = None
    ) -> None:
        self._account_id = account_id
        self._scope = scope


class GraphEntries(BaseModel):
    nodes: list[Node] = []
    edges: list[Edge] = Field(default_factory=list)


class Graph(CommonGraph):
    graph: GraphEntries
    metadata: MetaData = Field(default_factory=MetaData)

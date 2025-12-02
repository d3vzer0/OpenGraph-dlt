from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, computed_field
from opengraph_dlt.sources.aws.lookup import AWSLookup
from opengraph_dlt.sources.shared.models.graph import MetaData, Graph as CommonGraph
from opengraph_dlt.sources.shared.guid import Collector
from opengraph_dlt.sources.shared.models.entries import Node as BaseNode, Edge
from abc import ABC
from datetime import datetime
from typing import Optional
from enum import Enum
import uuid
from functools import cache, lru_cache


class NodeTypes(str, Enum):
    AWSUser = "AWSUser"
    AWSGroup = "AWSGroup"
    AWSRole = "AWSRole"
    AWSIdentityProvider = "AWSIdentityProvider"
    AWSEC2Instance = "AWSEC2Instance"
    AWSPolicy = "AWSPolicy"
    AWSInlinePolicy = "AWSInlinePolicy"
    AWSEKSCluster = "AWSEKSCluster"


class AWSCollector(Collector):

    @staticmethod
    @lru_cache(maxsize=65536)
    def guid(
        name: str,
        node_type: NodeTypes | str,
        account_id,
        scope: Optional[str] = "global",
    ):
        type_value = node_type.value if isinstance(node_type, NodeTypes) else node_type
        uuid_namespace = uuid.NAMESPACE_DNS
        resource_path = f"{name}.{type_value}.{account_id}.{scope}"
        return str(uuid.uuid5(uuid_namespace, resource_path))

    @staticmethod
    @cache
    def gen_node_type(node_type: str) -> str:
        pascal_case = "".join(x for x in node_type.title() if not x.isspace())
        return f"AWS{pascal_case}".replace(":", "")


class BaseResource(BaseModel):
    _lookup: AWSLookup = PrivateAttr()


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


class Node(BaseNode):
    properties: NodeProperties
    _account_id: Optional[str] = PrivateAttr(default=None)
    _scope: Optional[str] = PrivateAttr(default=None)

    @computed_field
    @property
    def id(self) -> str:
        account = self.properties.aws_account_id or self._account_id
        name = self.properties.arn if self.properties.arn else self.properties.name
        return AWSCollector.guid(
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

from pydantic import BaseModel, field_validator
from datetime import datetime
from opengraph_dlt.sources.kubernetes.models.graph import (
    Node,
    NodeProperties,
    NodeTypes,
    KubernetesCollector,
    BaseResource,
)
from opengraph_dlt.sources.shared.models.entries import Edge, EdgePath
import json


class Secret(BaseModel):
    field_path: str | None = None
    name: str
    namespace: str | None = None
    uid: str | None = None


class Subject(BaseModel):
    api_group: str | None = None
    kind: str
    name: str
    namespace: str | None = None


class RoleRef(BaseModel):
    api_group: str
    kind: str
    name: str


class Metadata(BaseModel):
    name: str
    uid: str
    namespace: str
    creation_timestamp: datetime
    labels: dict | None = None


class ExtendedProperties(NodeProperties):
    namespace: str
    bla: str | None = None


class ServiceAccountNode(Node):
    properties: ExtendedProperties


class ServiceAccount(BaseResource):
    kind: str | None = "ServiceAccount"
    metadata: Metadata
    automount_service_account_token: bool | None = None
    secrets: list[Secret] | None = None
    exists: bool = True

    @field_validator("kind", mode="before")
    def set_default_if_none(cls, v):
        return v if v is not None else "ServiceAccount"

    @property
    def as_node(self) -> "ServiceAccountNode":
        properties = ExtendedProperties(
            name=self.metadata.name,
            displayname=self.metadata.name,
            namespace=self.metadata.namespace,
            uid=self.metadata.uid,
        )
        return ServiceAccountNode(kinds=["KubeServiceAccount"], properties=properties)

    @property
    def _namespace_edge(self):
        target_id = KubernetesCollector.guid(
            self.metadata.namespace, NodeTypes.KubeNamespace, self._cluster
        )
        start_path = EdgePath(value=self.as_node.id, match_by="id")
        end_path = EdgePath(value=target_id, match_by="id")
        edge = Edge(kind="KubeBelongsTo", start=start_path, end=end_path)
        return edge

    @property
    def _authenticated_group_edge(self):
        target_id = KubernetesCollector.guid(
            "system:serviceaccounts", NodeTypes.KubeGroup, self._cluster
        )
        start_path = EdgePath(value=self.as_node.id, match_by="id")
        end_path = EdgePath(value=target_id, match_by="id")
        edge = Edge(kind="KubeMemberOf", start=start_path, end=end_path)
        return edge

    @property
    def _service_accounts_edge(self):
        target_id = KubernetesCollector.guid(
            "system:serviceaccounts", NodeTypes.KubeServiceAccount, self._cluster
        )
        start_path = EdgePath(value=self.as_node.id, match_by="id")
        end_path = EdgePath(value=target_id, match_by="id")
        edge = Edge(kind="KubeMemberOf", start=start_path, end=end_path)
        return edge

    @property
    def edges(self) -> list:
        return [
            self._namespace_edge,
            self._authenticated_group_edge,
            self._service_accounts_edge,
        ]

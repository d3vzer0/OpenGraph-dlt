from pydantic import BaseModel, field_validator
from datetime import datetime
from sources.kubernetes.models.graph import (
    Node,
    NodeProperties,
    NodeTypes,
    KubernetesCollector,
)
from sources.shared.models.entries import Edge, EdgePath
import json


class Secret(BaseModel):
    field_path: str
    name: str
    namespace: str
    uid: str


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


class ServiceAccount(BaseModel):
    kind: str | None = "ServiceAccount"
    metadata: Metadata
    automount_service_account_token: bool | None = None
    secrets: list[Secret] | None = None
    exists: bool = True

    @field_validator("kind", mode="before")
    def set_default_if_none(cls, v):
        return v if v is not None else "ServiceAccount"

    @field_validator("metadata", mode="before")
    @classmethod
    def parse_json_string(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v


class ExtendedProperties(NodeProperties):
    namespace: str
    bla: str | None = None


class ServiceAccountNode(Node):
    properties: ExtendedProperties

    @property
    def _namespace_edge(self):
        target_id = KubernetesCollector.guid(
            self.properties.namespace, NodeTypes.KubeNamespace, self._cluster
        )
        start_path = EdgePath(value=self.id, match_by="id")
        end_path = EdgePath(value=target_id, match_by="id")
        edge = Edge(kind="KubeBelongsTo", start=start_path, end=end_path)
        return edge

    @property
    def _authenticated_group_edge(self):
        target_id = KubernetesCollector.guid(
            "system:serviceaccounts", NodeTypes.KubeGroup, self._cluster
        )
        start_path = EdgePath(value=self.id, match_by="id")
        end_path = EdgePath(value=target_id, match_by="id")
        edge = Edge(kind="KubeMemberOf", start=start_path, end=end_path)
        return edge

    @property
    def _service_accounts_edge(self):
        target_id = KubernetesCollector.guid(
            "system:serviceaccounts", NodeTypes.KubeServiceAccount, self._cluster
        )
        start_path = EdgePath(value=self.id, match_by="id")
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

    @classmethod
    def from_input(cls, **kwargs) -> "ServiceAccountNode":
        model = ServiceAccount(**kwargs)
        properties = ExtendedProperties(
            name=model.metadata.name,
            displayname=model.metadata.name,
            namespace=model.metadata.namespace,
            uid=model.metadata.uid,
        )
        return cls(kinds=["KubeServiceAccount"], properties=properties)

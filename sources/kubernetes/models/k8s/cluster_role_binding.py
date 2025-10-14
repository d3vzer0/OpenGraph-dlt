from pydantic import BaseModel, field_validator
from datetime import datetime
from ..entries import (
    Node,
    NodeProperties,
    Edge,
    EdgeProperties,
    EdgePath,
)
from sources.kubernetes.utils.guid import get_guid, NodeTypes
import json


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
    creation_timestamp: datetime | None = None
    labels: dict | None = None
    namespace: str | None = ""


class ClusterRoleBinding(BaseModel):
    kind: str | None = "ClusterRoleBinding"
    metadata: Metadata
    role_ref: RoleRef
    subjects: list[Subject] = []

    @field_validator("kind", mode="before")
    def set_default_if_none(cls, v):
        return v if v is not None else "ClusterRoleBinding"

    @field_validator("role_ref", mode="before")
    def validate_role_ref(cls, value):
        if isinstance(value, str):
            value = json.loads(value)
        return value

    @field_validator("subjects", mode="before")
    def validate_subjects(cls, value):
        if isinstance(value, str):
            value = json.loads(value)
        return value or []

    @field_validator("metadata", mode="before")
    @classmethod
    def parse_json_string(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v


class ExtendedProperties(NodeProperties):
    role_ref: str
    subjects: list[Subject] = []

    @field_validator("subjects", mode="before")
    def validate_subjects(cls, v):
        if not v:
            return []
        return v


class ClusterRoleBindingNode(Node):
    properties: ExtendedProperties

    @property
    def _role_path(self):
        role_id = get_guid(
            self.properties.role_ref,
            NodeTypes.KubeClusterRole,
            self._cluster,
        )
        edge_path = EdgePath(value=role_id, match_by="id")
        return edge_path

    @property
    def _role_edge(self):
        start_path = EdgePath(value=self.id, match_by="id")
        return Edge(kind="KubeReferencesRole", start=start_path, end=self._role_path)

    def _service_account_path(self, target: str, namespace):
        target_id = get_guid(
            target, NodeTypes.KubeServiceAccount, self._cluster, namespace
        )
        return EdgePath(value=target_id, match_by="id")

    def _get_target_user(self, target_name: str) -> "EdgePath":
        target_id = get_guid(target_name, NodeTypes.KubeUser, self._cluster)
        return EdgePath(value=target_id, match_by="id")

    def _get_target_group(self, target_name: str) -> "EdgePath":
        target_id = get_guid(target_name, NodeTypes.KubeGroup, self._cluster)
        return EdgePath(value=target_id, match_by="id")

    @property
    def _subjects(self):
        edges = []
        rb_path = EdgePath(value=self.id, match_by="id")
        for target in self.properties.subjects:
            if target.kind == "ServiceAccount":
                get_sa_path = self._service_account_path(target.name, target.namespace)
                sa_edge = Edge(kind="KubeAuthorizes", start=rb_path, end=get_sa_path)

                role_edge = Edge(
                    kind="KubeInheritsRole",
                    start=get_sa_path,
                    end=self._role_path,
                    properties=EdgeProperties(composed=True),
                )

                edges.append(sa_edge)
                edges.append(role_edge)

            elif target.kind == "User":
                end_path = self._get_target_user(target.name)
                edges.append(Edge(kind="KubeAuthorizes", start=rb_path, end=end_path))

            elif target.kind == "Group":
                end_path = self._get_target_group(target.name)
                edges.append(Edge(kind="KubeAuthorizes", start=rb_path, end=end_path))

        return edges

    @property
    def edges(self):
        return [self._role_edge, *self._subjects]

    @classmethod
    def from_input(cls, **kwargs) -> "ClusterRoleBindingNode":
        model = ClusterRoleBinding(**kwargs)
        properties = ExtendedProperties(
            name=model.metadata.name,
            displayname=model.metadata.name,
            role_ref=model.role_ref.name,
            subjects=model.subjects,
            uid=model.metadata.uid,
            namespace=None,
        )
        return cls(
            kinds=["KubeClusterRoleBinding", "KubeRoleBinding"],
            properties=properties,
        )

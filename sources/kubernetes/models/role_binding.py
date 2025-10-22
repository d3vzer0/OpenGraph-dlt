from pydantic import BaseModel, field_validator
from datetime import datetime
from sources.kubernetes.models.graph import Node, NodeProperties
from sources.shared.models.entries import Edge, EdgePath
from sources.kubernetes.utils.guid import get_guid
from sources.kubernetes.utils.guid import NodeTypes
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
    namespace: str
    creation_timestamp: datetime | None = None
    labels: dict | None = None


class RoleBinding(BaseModel):
    kind: str | None = "RoleBinding"
    subjects: list[Subject] = []
    metadata: Metadata
    role_ref: RoleRef
    subjects: list[Subject]

    @field_validator("kind", mode="before")
    def set_default_if_none(cls, v):
        return v if v is not None else "RoleBinding"

    @field_validator("subjects", mode="before")
    def validate_subjects(cls, value):
        if isinstance(value, str):
            value = json.loads(value)
        return value or []

    @field_validator("role_ref", mode="before")
    def validate_role_ref(cls, value):
        if isinstance(value, str):
            value = json.loads(value)
        return value

    @field_validator("metadata", mode="before")
    @classmethod
    def parse_json_string(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v


class ExtendedProperties(NodeProperties):
    # namespace: str
    role_ref: str
    subjects: list[Subject]


class RoleBindingNode(Node):
    properties: ExtendedProperties

    def _get_target_user(self, target_name: str) -> "EdgePath":
        target_id = get_guid(target_name, NodeTypes.KubeUser, self._cluster)
        return EdgePath(value=target_id, match_by="id")

    def _get_target_group(self, target_name: str) -> "EdgePath":
        target_id = get_guid(target_name, NodeTypes.KubeGroup, self._cluster)
        return EdgePath(value=target_id, match_by="id")

    def _service_account_path(self, target: str, namespace):
        target_id = get_guid(
            target, NodeTypes.KubeServiceAccount, self._cluster, namespace
        )
        return EdgePath(value=target_id, match_by="id")

    @property
    def _namespace_edge(self):
        target_id = get_guid(
            self.properties.namespace, NodeTypes.KubeNamespace, self._cluster
        )
        start_path = EdgePath(value=self.id, match_by="id")
        end_path = EdgePath(value=target_id, match_by="id")
        edge = Edge(kind="KubeBelongsTo", start=start_path, end=end_path)
        return edge

    @property
    def _role_path(self):
        role_id = get_guid(
            self.properties.role_ref,
            NodeTypes.KubeScopedRole,
            self._cluster,
            namespace=self.properties.namespace,
        )
        edge_path = EdgePath(value=role_id, match_by="id")
        return edge_path

    @property
    def _role_edge(self):
        start_path = EdgePath(value=self.id, match_by="id")
        edge = Edge(kind="KubeReferencesRole", start=start_path, end=self._role_path)
        return edge

    @property
    def _subjects(self):
        edges = []
        rb_path = EdgePath(value=self.id, match_by="id")
        for target in self.properties.subjects:
            if target.kind == "ServiceAccount":
                namespace = (
                    target.namespace if target.namespace else self.properties.namespace
                )
                get_sa_path = self._service_account_path(target.name, namespace)
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

            else:
                print(
                    f"Unsupported subject kind: {target.kind} in RoleBinding {self.properties.name}"
                )

        return edges

    @property
    def edges(self):
        all_edges = self._subjects
        return [self._namespace_edge, self._role_edge, *all_edges]

    @classmethod
    def from_input(cls, **kwargs) -> "RoleBindingNode":
        model = RoleBinding(**kwargs)
        properties = ExtendedProperties(
            name=model.metadata.name,
            displayname=model.metadata.name,
            # objectid=model.metadata.uid,
            namespace=model.metadata.namespace,
            role_ref=model.role_ref.name,
            subjects=model.subjects,
            uid=model.metadata.uid,
        )
        return cls(
            kinds=["KubeScopedRoleBinding", "KubeRoleBinding"],
            properties=properties,
        )

from pydantic import BaseModel, field_validator
from datetime import datetime
from opengraph_dlt.sources.kubernetes.models.graph import (
    Node,
    NodeProperties,
    NodeTypes,
    KubernetesCollector,
    BaseResource,
)
from opengraph_dlt.sources.shared.models.entries import Edge, EdgePath, EdgeProperties
from opengraph_dlt.sources.shared.docs import graph_resource, NodeDef, EdgeDef
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


class ExtendedProperties(NodeProperties):
    # namespace: str
    role_ref: str
    subjects: list[Subject]


class RoleBindingNode(Node):
    properties: ExtendedProperties


@graph_resource(
    node=NodeDef(
        kind=NodeTypes.KubeScopedRoleBinding.value,
        description="Namespaced role binding",
    ),
    edges=[
        EdgeDef(
            start=NodeTypes.KubeScopedRoleBinding.value,
            end=NodeTypes.KubeNamespace.value,
            kind="KubeBelongsTo",
            description="RoleBinding scoped to a namespace",
        ),
        EdgeDef(
            start=NodeTypes.KubeScopedRoleBinding.value,
            end=NodeTypes.KubeScopedRole.value,
            kind="KubeReferencesRole",
            description="Binding references a role",
        ),
        EdgeDef(
            start=NodeTypes.KubeScopedRoleBinding.value,
            end="Kube{Subject}",
            kind="KubeAuthorizes",
            description="Binding authorizes subjects (ServiceAccount/User/Group)",
        ),
        EdgeDef(
            start=NodeTypes.KubeServiceAccount.value,
            end=NodeTypes.KubeScopedRole.value,
            kind="KubeInheritsRole",
            description="ServiceAccount inherits role via binding",
        ),
    ],
)
class RoleBinding(BaseResource):
    kind: str | None = "RoleBinding"
    subjects: list[Subject] = []
    metadata: Metadata
    role_ref: RoleRef
    subjects: list[Subject]

    @field_validator("kind", mode="before")
    def set_default_if_none(cls, v):
        return v if v is not None else "RoleBinding"

    @property
    def as_node(self) -> "RoleBindingNode":
        properties = ExtendedProperties(
            name=self.metadata.name,
            displayname=self.metadata.name,
            namespace=self.metadata.namespace,
            role_ref=self.role_ref.name,
            subjects=self.subjects,
            uid=self.metadata.uid,
        )
        return RoleBindingNode(
            kinds=["KubeScopedRoleBinding", "KubeRoleBinding"],
            properties=properties,
        )

    def _get_target_user(self, target_name: str) -> "EdgePath":
        target_id = KubernetesCollector.guid(
            target_name, NodeTypes.KubeUser, self._cluster
        )
        return EdgePath(value=target_id, match_by="id")

    def _get_target_group(self, target_name: str) -> "EdgePath":
        target_id = KubernetesCollector.guid(
            target_name, NodeTypes.KubeGroup, self._cluster
        )
        return EdgePath(value=target_id, match_by="id")

    def _service_account_path(self, target: str, namespace):
        target_id = KubernetesCollector.guid(
            target, NodeTypes.KubeServiceAccount, self._cluster, namespace
        )
        return EdgePath(value=target_id, match_by="id")

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
    def _role_path(self):
        role_id = KubernetesCollector.guid(
            self.role_ref.name,
            NodeTypes.KubeScopedRole,
            self._cluster,
            namespace=self.metadata.namespace,
        )
        edge_path = EdgePath(value=role_id, match_by="id")
        return edge_path

    @property
    def _role_edge(self):
        start_path = EdgePath(value=self.as_node.id, match_by="id")
        edge = Edge(kind="KubeReferencesRole", start=start_path, end=self._role_path)
        return edge

    @property
    def _subjects(self):
        edges = []
        rb_path = EdgePath(value=self.as_node.id, match_by="id")
        for target in self.subjects:
            if target.kind == "ServiceAccount":
                namespace = (
                    target.namespace if target.namespace else self.metadata.namespace
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
                    f"Unsupported subject kind: {target.kind} in RoleBinding {self.metadata.name}"
                )

        return edges

    @property
    def edges(self):
        all_edges = self._subjects
        return [self._namespace_edge, self._role_edge, *all_edges]

from pydantic import BaseModel, ConfigDict
from datetime import datetime
from pydantic import Field
from opengraph_dlt.sources.kubernetes.models.graph import (
    Node,
    NodeProperties,
    NodeTypes,
    KubernetesCollector,
    BaseResource,
)
from opengraph_dlt.sources.shared.models.entries import Edge, EdgePath
from opengraph_dlt.sources.shared.docs import graph_resource, NodeDef, EdgeDef


VERB_TO_PERMISSION = {
    "get": "KubeCanGet",
    "list": "KubeCanList",
    "watch": "KubeCanWatch",
    "create": "KubeCanCreate",
    "update": "KubeCanUpdate",
    "patch": "KubeCanPatch",
    "delete": "KubeCanDelete",
    "deletecollection": "KubeCanDeleteCollection",
    "proxy": "KubeCanProxy",
    "*": "KubeCanAll",
}


class Metadata(BaseModel):
    name: str
    uid: str
    namespace: str
    creation_timestamp: datetime | None = None
    labels: dict = {}
    annotations: dict = {}


class SourceRole(BaseModel):
    name: str
    uid: str
    permissions: list[str]


class ExtendedProperties(NodeProperties):
    model_config = ConfigDict(extra="allow")
    # namespace: str


class DynamicNode(Node):
    properties: ExtendedProperties
    source_role_uid: str = Field(exclude=True)
    source_role_permissions: list[str] = Field(exclude=True)


@graph_resource(
    node=NodeDef(kind="Kube{DynamicKind}", description="Dynamically discovered resource"),
    edges=[
        EdgeDef(
            start="Kube{DynamicKind}",
            end=NodeTypes.KubeNamespace.value,
            kind="KubeBelongsTo",
            description="Resource belongs to a namespace",
        ),
        EdgeDef(
            start=NodeTypes.KubeScopedRole.value,
            end="Kube{DynamicKind}",
            kind="KubeCan*",
            description="Permissions from source role to dynamic resource",
        ),
    ],
)
class DynamicResource(BaseResource):
    kind: str
    role: SourceRole
    metadata: Metadata

    @property
    def as_node(self) -> "DynamicNode":
        properties = ExtendedProperties(
            name=self.metadata.name,
            displayname=self.metadata.name,
            namespace=self.metadata.namespace,
            uid=self.metadata.uid,
            **self.metadata.labels,
            cluster=self._cluster,
        )
        return DynamicNode(
            kinds=[f"Kube{self.kind}"],
            properties=properties,
            source_role_uid=self.role.uid,
            source_role_permissions=self.role.permissions,
        )

    @property
    def _namespace_edge(self):
        # target_id = self._lookup.namespaces(self.properties.namespace)
        target_id = KubernetesCollector.guid(
            self.metadata.namespace, NodeTypes.KubeNamespace, self._cluster
        )
        start_path = EdgePath(value=self.as_node.id, match_by="id")
        end_path = EdgePath(value=target_id, match_by="id")
        edge = Edge(kind="KubeBelongsTo", start=start_path, end=end_path)
        return edge

    @property
    def _role_edge(self):
        role_edges = []
        for permission in self.role.permissions:
            end_path = EdgePath(value=self.as_node.id, match_by="id")
            start_path = EdgePath(value=self.role.uid, match_by="id")
            mapped_permission = VERB_TO_PERMISSION[permission]
            edge = Edge(kind=mapped_permission, start=start_path, end=end_path)
            role_edges.append(edge)
        return role_edges

    @property
    def edges(self):
        return [*self._role_edge, self._namespace_edge]

from pydantic import BaseModel, ConfigDict
from datetime import datetime
from pydantic import Field
from sources.kubernetes.models.graph import Node, NodeProperties, NodeTypes, gen_guid
from sources.shared.models.entries import Edge, EdgePath


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


class DynamicResource(BaseModel):
    kind: str
    role: SourceRole
    metadata: Metadata


class ExtendedProperties(NodeProperties):
    model_config = ConfigDict(extra="allow")
    # namespace: str


class DynamicNode(Node):
    properties: ExtendedProperties
    source_role_uid: str = Field(exclude=True)
    source_role_permissions: list[str] = Field(exclude=True)

    @property
    def _namespace_edge(self):
        # target_id = self._lookup.namespaces(self.properties.namespace)
        target_id = gen_guid(
            self.properties.namespace, NodeTypes.KubeNamespace, self._cluster
        )
        start_path = EdgePath(value=self.id, match_by="id")
        end_path = EdgePath(value=target_id, match_by="id")
        edge = Edge(kind="KubeBelongsTo", start=start_path, end=end_path)
        return edge

    @property
    def _role_edge(self):
        role_edges = []
        for permission in self.source_role_permissions:
            end_path = EdgePath(value=self.id, match_by="id")
            # target_id = self.source_role_uid
            # target_id =
            start_path = EdgePath(value=target_id, match_by="id")
            mapped_permission = VERB_TO_PERMISSION[permission]
            edge = Edge(kind=mapped_permission, start=start_path, end=end_path)
            role_edges.append(edge)
        return role_edges

    @property
    def edges(self):
        return [*self._role_edge, self._namespace_edge]

    @classmethod
    def from_input(cls, **kwargs) -> "DynamicNode":
        kube_resource = DynamicResource(**kwargs)
        properties = ExtendedProperties(
            name=kube_resource.metadata.name,
            displayname=kube_resource.metadata.name,
            namespace=kube_resource.metadata.namespace,
            **kube_resource.metadata.labels,
        )
        return cls(
            kinds=[f"Kube{kube_resource.kind}"],
            properties=properties,
            source_role_uid=kube_resource.role.uid,
            source_role_permissions=kube_resource.role.permissions,
        )

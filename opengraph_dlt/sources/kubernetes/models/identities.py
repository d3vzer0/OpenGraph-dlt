from pydantic import BaseModel, computed_field
from opengraph_dlt.sources.kubernetes.models.graph import (
    Node,
    NodeProperties,
    NodeTypes,
    KubernetesCollector,
)
from opengraph_dlt.sources.shared.models.entries import Edge, EdgePath
from opengraph_dlt.sources.shared.docs import graph_resource, NodeDef, EdgeDef


class User(BaseModel):
    name: str
    api_group: str
    kind: str = "User"

    @computed_field
    @property
    def uid(self) -> str:
        return KubernetesCollector.guid(self.name, NodeTypes.KubeUser, "")

    @graph_resource(
        node=NodeDef(kind=NodeTypes.KubeUser.value, description="Kubernetes user"),
        edges=[
            EdgeDef(
                start=NodeTypes.KubeUser.value,
                end=NodeTypes.KubeGroup.value,
                kind="KubeMemberOf",
                description="User is a member of system groups via bindings",
            )
        ],
    )
    @property
    def as_node(self) -> "UserNode":
        properties = NodeProperties(
            name=self.name, displayname=self.name, uid=self.uid, namespace=None
        )
        return UserNode(kinds=["KubeUser"], properties=properties)


class Group(BaseModel):
    name: str
    api_group: str
    kind: str = "Group"

    @computed_field
    @property
    def uid(self) -> str:
        return KubernetesCollector.guid(self.name, NodeTypes.KubeGroup, "")

    @graph_resource(
        node=NodeDef(kind=NodeTypes.KubeGroup.value, description="Kubernetes group"),
        edges=[],
    )
    @property
    def as_node(self) -> "GroupNode":
        properties = NodeProperties(
            name=self.name, displayname=self.name, uid=self.uid, namespace=None
        )
        return GroupNode(kinds=["KubeGroup"], properties=properties)


class UserNode(Node):

    @property
    def _authenticated_group_edge(self):
        # target_id = self._lookup.groups("system:authenticated")
        target_id = KubernetesCollector.guid(
            "system:authenticated", NodeTypes.KubeGroup, self._cluster
        )
        start_path = EdgePath(value=self.id, match_by="id")
        end_path = EdgePath(value=target_id, match_by="id")
        edge = Edge(kind="KubeMemberOf", start=start_path, end=end_path)
        return edge

    @property
    def edges(self):
        return [self._authenticated_group_edge]


class GroupNode(Node):
    @property
    def edges(self):
        return []

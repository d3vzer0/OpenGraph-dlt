from pydantic import BaseModel, computed_field, ConfigDict
from opengraph_dlt.sources.kubernetes.models.graph import (
    Node,
    NodeProperties,
    NodeTypes,
    KubernetesCollector,
    BaseResource,
)
from opengraph_dlt.sources.shared.models.entries import Edge, EdgePath
from opengraph_dlt.sources.shared.docs import graph_resource, NodeDef, EdgeDef


class ExtendedProperties(NodeProperties):
    model_config = ConfigDict(extra="allow")
    node_name: str


class VolumeNode(Node):
    properties: ExtendedProperties


@graph_resource(
    node=NodeDef(kind=NodeTypes.KubeVolume.value, description="HostPath-based volume"),
    edges=[
        EdgeDef(
            start=NodeTypes.KubeVolume.value,
            end=NodeTypes.KubeNode.value,
            kind="KubeHostedOn",
            description="Volume resides on the physical/virtual node",
        )
    ],
)
class Volume(BaseResource):
    node_name: str
    path: str
    # cluster: str

    @computed_field
    @property
    def name(self) -> str:
        return f"fs://{self.node_name}{self.path}"

    @computed_field
    @property
    def uid(self) -> str:
        return KubernetesCollector.guid(self.name, NodeTypes.KubeVolume, "")

    @property
    def as_node(self) -> "VolumeNode":
        properties = ExtendedProperties(
            name=self.name,
            displayname=self.name,
            node_name=self.node_name,
            namespace=None,
            uid=self.uid,
            cluster=self._cluster,
        )
        return VolumeNode(kinds=["KubeVolume"], properties=properties)

    @property
    def _node_edge(self):
        start_path = EdgePath(value=self.as_node.id, match_by="id")
        end_path_id = KubernetesCollector.guid(
            self.node_name, NodeTypes.KubeNode, self._cluster
        )
        end_path = EdgePath(value=end_path_id, match_by="id")
        edge = Edge(kind="KubeHostedOn", start=start_path, end=end_path)
        return edge

    @property
    def edges(self):
        return [self._node_edge]

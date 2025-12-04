from collections.abc import Iterator

from pydantic import BaseModel, field_validator
from datetime import datetime
from opengraph_dlt.sources.kubernetes.models.graph import (
    NodeProperties,
    Node as GraphNode,
    NodeTypes,
    KubernetesCollector,
    BaseResource,
)
from opengraph_dlt.sources.shared.models.entries import Edge, EdgePath
from opengraph_dlt.sources.shared.docs import graph_resource, NodeDef, EdgeDef


class Metadata(BaseModel):
    name: str
    uid: str
    creation_timestamp: datetime
    labels: dict = {}


class NodeOutput(GraphNode): ...


@graph_resource(
    node=NodeDef(kind=NodeTypes.KubeNode.value, description="Kubernetes node"),
    edges=[
        EdgeDef(
            start=NodeTypes.KubeNode.value,
            end=NodeTypes.KubeCluster.value,
            kind="KubeBelongsTo",
            description="Node belongs to the cluster",
        ),
        # EdgeDef(
        #     start=NodeTypes.KubeNode.value,
        #     end=NodeTypes.KubeGroup.value,
        #     kind="KubeMemberOf",
        #     description="Groups",
        # ),
    ],
)
class KubeNode(BaseResource):
    metadata: Metadata
    kind: str | None = "Node"

    @field_validator("kind", mode="before")
    def set_default_if_none(cls, v):
        return v if v is not None else "Node"

    @property
    def as_node(self) -> "NodeOutput":
        properties = NodeProperties(
            name=self.metadata.name,
            displayname=self.metadata.name,
            uid=self.metadata.uid,
            namespace=None,
            cluster=self._cluster,
        )
        return NodeOutput(kinds=["KubeNode"], properties=properties)

    @property
    def _authenticated_group_edge(self):
        target_id = KubernetesCollector.guid(
            "system:authenticated", NodeTypes.KubeGroup, self._cluster
        )
        start_path = EdgePath(value=self.as_node.id, match_by="id")
        end_path = EdgePath(value=target_id, match_by="id")
        edge = Edge(kind="KubeMemberOf", start=start_path, end=end_path)
        return edge

    @property
    def _nodes_group_edge(self):
        target_id = KubernetesCollector.guid(
            "system:nodes", NodeTypes.KubeGroup, self._cluster
        )
        start_path = EdgePath(value=self.as_node.id, match_by="id")
        end_path = EdgePath(value=target_id, match_by="id")
        edge = Edge(kind="KubeMemberOf", start=start_path, end=end_path)
        return edge

    @property
    def _cluster_edge(self):
        target_id = KubernetesCollector.guid(
            self._cluster, NodeTypes.KubeCluster, self._cluster
        )
        start_path = EdgePath(value=self.as_node.id, match_by="id")
        end_path = EdgePath(value=target_id, match_by="id")
        edge = Edge(kind="KubeBelongsTo", start=start_path, end=end_path)
        return edge

    @property
    def edges(self) -> Iterator[Edge]:
        yield self._cluster_edge
        yield self._authenticated_group_edge
        yield self._nodes_group_edge

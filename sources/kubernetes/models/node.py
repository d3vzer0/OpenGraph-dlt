from pydantic import BaseModel, field_validator
from datetime import datetime
from sources.kubernetes.models.graph import (
    NodeProperties,
    Node as GraphNode,
    NodeTypes,
    KubernetesCollector,
)
from sources.shared.models.entries import Edge, EdgePath


class Metadata(BaseModel):
    name: str
    uid: str
    creation_timestamp: datetime
    labels: dict = {}


class Node(BaseModel):
    metadata: Metadata
    kind: str | None = "Node"

    @field_validator("kind", mode="before")
    def set_default_if_none(cls, v):
        return v if v is not None else "Node"


class NodeOutput(GraphNode):

    @property
    def _authenticated_group_edge(self):
        target_id = KubernetesCollector.guid(
            "system:authenticated", NodeTypes.KubeGroup, self._cluster
        )
        start_path = EdgePath(value=self.id, match_by="id")
        end_path = EdgePath(value=target_id, match_by="id")
        edge = Edge(kind="KubeMemberOf", start=start_path, end=end_path)
        return edge

    @property
    def _nodes_group_edge(self):
        target_id = KubernetesCollector.guid(
            "system:nodes", NodeTypes.KubeGroup, self._cluster
        )
        start_path = EdgePath(value=self.id, match_by="id")
        end_path = EdgePath(value=target_id, match_by="id")
        edge = Edge(kind="KubeMemberOf", start=start_path, end=end_path)
        return edge

    @property
    def _cluster_edge(self):
        target_id = KubernetesCollector.guid(
            self._cluster, NodeTypes.KubeCluster, self._cluster
        )
        start_path = EdgePath(value=self.id, match_by="id")
        end_path = EdgePath(value=target_id, match_by="id")
        edge = Edge(kind="KubeBelongsTo", start=start_path, end=end_path)
        return edge

    @property
    def edges(self):
        return [
            self._cluster_edge,
            self._authenticated_group_edge,
            self._nodes_group_edge,
        ]

    @classmethod
    def from_input(cls, **kwargs) -> "NodeOutput":
        node_out = Node(**kwargs)
        properties = NodeProperties(
            name=node_out.metadata.name,
            displayname=node_out.metadata.name,
            uid=node_out.metadata.uid,
            namespace=None,
        )
        return cls(kinds=["KubeNode"], properties=properties)

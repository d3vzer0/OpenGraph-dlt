from collections.abc import Iterator

from pydantic import BaseModel, field_validator
from datetime import datetime
from .cluster import Cluster
from opengraph_dlt.sources.kubernetes.models.graph import (
    Node,
    NodeProperties,
    BaseResource,
)
from opengraph_dlt.sources.shared.models.entries import Edge, EdgePath
from opengraph_dlt.sources.shared.docs import graph_resource, NodeDef, EdgeDef
import json


class Metadata(BaseModel):
    name: str
    uid: str
    creation_timestamp: datetime | None = None
    labels: dict


class NamespaceNode(Node):
    pass


@graph_resource(
    node=NodeDef(kind="KubeNamespace", description="Kubernetes Namespace node"),
    edges=[
        EdgeDef(
            start="KubeNamespace",
            end="KubeCluster",
            kind="KubeBelongsTo",
            description="Namespace belongs to the cluster",
        )
    ],
)
class Namespace(BaseResource):
    metadata: Metadata
    kind: str | None = "Namespace"

    @field_validator("kind", mode="before")
    @classmethod
    def set_default_if_none(cls, v):
        return v if v is not None else "Namespace"

    @property
    def as_node(self) -> "NamespaceNode":
        properties = NodeProperties(
            name=self.metadata.name,
            displayname=self.metadata.name,
            uid=self.metadata.uid,
            namespace=None,
            cluster=self._cluster,
        )
        return NamespaceNode(kinds=["KubeNamespace"], properties=properties)

    @property
    def _cluster_edge(self):
        start_path = EdgePath(value=self.as_node.id, match_by="id")
        cluster = Cluster(name=self._cluster)
        end_path = EdgePath(value=cluster.uid, match_by="id")
        edge = Edge(kind="KubeBelongsTo", start=start_path, end=end_path)
        return edge

    @property
    def edges(self) -> Iterator[Edge]:
        yield self._cluster_edge

from pydantic import BaseModel, field_validator
from datetime import datetime
from .cluster import Cluster
from sources.kubernetes.models.graph import Node, NodeProperties
from sources.shared.models.entries import Edge, EdgePath
import json


class Metadata(BaseModel):
    name: str
    uid: str
    creation_timestamp: datetime | None = None
    labels: dict


class Namespace(BaseModel):
    metadata: Metadata
    kind: str | None = "Namespace"

    @field_validator("kind", mode="before")
    @classmethod
    def set_default_if_none(cls, v):
        return v if v is not None else "Namespace"

    @field_validator("metadata", mode="before")
    @classmethod
    def parse_json_string(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v


class NamespaceNode(Node):

    @property
    def _cluster_edge(self):
        start_path = EdgePath(value=self.id, match_by="id")
        cluster = Cluster(name=self._cluster)
        end_path = EdgePath(value=cluster.uid, match_by="id")
        edge = Edge(kind="KubeBelongsTo", start=start_path, end=end_path)
        return edge

    @property
    def edges(self):
        return [self._cluster_edge]

    @classmethod
    def from_input(cls, **kwargs) -> "NamespaceNode":
        ns_node = Namespace(**kwargs)
        properties = NodeProperties(
            name=ns_node.metadata.name,
            displayname=ns_node.metadata.name,
            uid=ns_node.metadata.uid,
            namespace=None,
        )
        return cls(kinds=["KubeNamespace"], properties=properties)

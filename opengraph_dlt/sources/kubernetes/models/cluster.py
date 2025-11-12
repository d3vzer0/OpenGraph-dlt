from pydantic import BaseModel, computed_field
from opengraph_dlt.sources.kubernetes.models.graph import (
    Node,
    NodeProperties,
    NodeTypes,
    KubernetesCollector,
)


class Cluster(BaseModel):
    name: str
    kind: str = "Cluster"

    @computed_field
    @property
    def uid(self) -> str:
        return KubernetesCollector.guid(self.name, NodeTypes.KubeCluster, self.name)


class ClusterNode(Node):

    @property
    def edges(self):
        return []

    @classmethod
    def from_input(cls, **kwargs) -> "ClusterNode":
        cluster = Cluster(**kwargs)
        properties = NodeProperties(
            name=cluster.name, displayname=cluster.name, uid=cluster.uid, namespace=None
        )
        return cls(kinds=["KubeCluster"], properties=properties)

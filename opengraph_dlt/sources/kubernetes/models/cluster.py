from pydantic import BaseModel, computed_field
from opengraph_dlt.sources.kubernetes.models.graph import (
    Node,
    NodeProperties,
    NodeTypes,
    KubernetesCollector,
    BaseResource,
)


class ClusterNode(Node):
    pass


class Cluster(BaseResource):
    name: str
    kind: str = "Cluster"

    @computed_field
    @property
    def uid(self) -> str:
        return KubernetesCollector.guid(self.name, NodeTypes.KubeCluster, self.name)

    @property
    def as_node(self) -> "ClusterNode":
        properties = NodeProperties(
            name=self.name,
            displayname=self.name,
            uid=self.uid,
            namespace=None,
        )
        return ClusterNode(kinds=["KubeCluster"], properties=properties)

    @property
    def edges(self):
        return []

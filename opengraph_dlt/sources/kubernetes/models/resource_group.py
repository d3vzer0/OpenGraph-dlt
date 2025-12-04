from collections.abc import Iterator

from pydantic import BaseModel, computed_field
from opengraph_dlt.sources.kubernetes.models.graph import (
    Node,
    NodeProperties,
    NodeTypes,
    KubernetesCollector,
    BaseResource,
)
from typing import Optional
from opengraph_dlt.sources.shared.models.entries import Edge
from opengraph_dlt.sources.shared.docs import graph_resource, NodeDef


class GroupVersion(BaseModel):
    group_version: str
    version: str


class ResourceGroupNode(Node):
    pass


@graph_resource(
    node=NodeDef(
        kind=NodeTypes.KubeResourceGroup.value, description="Kubernetes API group"
    )
)
class ResourceGroup(BaseResource):
    name: str
    api_version: Optional[str] = None

    @computed_field
    @property
    def uid(self) -> str:
        return KubernetesCollector.guid(self.name, NodeTypes.KubeResourceGroup, "")

    @property
    def as_node(self) -> "ResourceGroupNode":
        properties = NodeProperties(
            name=self.name,
            displayname=self.name,
            uid=self.uid,
            namespace=None,
            cluster=self._cluster,
        )
        return ResourceGroupNode(kinds=["KubeResourceGroup"], properties=properties)

    @property
    def edges(self) -> Iterator[Edge]:
        yield from ()

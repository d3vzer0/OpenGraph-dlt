from pydantic import BaseModel, computed_field
from opengraph_dlt.sources.kubernetes.models.graph import (
    Node,
    NodeProperties,
    NodeTypes,
    KubernetesCollector,
    BaseResource,
)
from typing import Optional


class GroupVersion(BaseModel):
    group_version: str
    version: str


class ResourceGroupNode(Node):
    pass


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
            name=self.name, displayname=self.name, uid=self.uid, namespace=None
        )
        return ResourceGroupNode(kinds=["KubeResourceGroup"], properties=properties)

    @property
    def edges(self):
        return []

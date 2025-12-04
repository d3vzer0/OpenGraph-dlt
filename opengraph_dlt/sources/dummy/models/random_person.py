from collections.abc import Iterator

from opengraph_dlt.sources.dummy.models.graph import (
    Node,
    NodeProperties,
    BaseResource,
)
from opengraph_dlt.sources.shared.models.entries import Edge, EdgePath, EdgeProperties
from opengraph_dlt.sources.shared.docs import graph_resource, NodeDef, EdgeDef


class ExtendedProperties(NodeProperties):
    address: str


class RandomPersonNode(Node):
    properties: ExtendedProperties


@graph_resource(
    node=NodeDef(
        kind="RandomPerson",
        description="Random person node",
    ),
    edges=[
        # EdgeDef(
        #     start=NodeTypes.KubeClusterRoleBinding.value,
        #     end=NodeTypes.KubeClusterRole.value,
        #     kind="KubeReferencesRole",
        #     description="Binding references a ClusterRole",
        # ),
    ],
)
class RandomPerson(BaseResource):
    name: str
    address: str

    @property
    def as_node(self) -> "RandomPersonNode":
        properties = ExtendedProperties(
            name=self.name,
            address=self.address,
            displayname=self.name,
        )
        return RandomPersonNode(
            kinds=["RandomPersonNode"],
            properties=properties,
        )

    @property
    def edges(self) -> Iterator[Edge]:
        yield from ()

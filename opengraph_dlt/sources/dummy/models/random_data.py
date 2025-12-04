from collections.abc import Iterator
from opengraph_dlt.sources.dummy.models.graph import (
    Node,
    NodeProperties,
    BaseResource,
)
from opengraph_dlt.sources.shared.models.entries import Edge, EdgePath
from opengraph_dlt.sources.shared.docs import graph_resource, NodeDef, EdgeDef


class ExtendedProperties(NodeProperties):
    secondary: float


class RandomDataNode(Node):
    properties: ExtendedProperties


@graph_resource(
    node=NodeDef(
        kind="RandomData",
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
class RandomData(BaseResource):
    primary: float
    secondary: float

    @property
    def as_node(self) -> "RandomDataNode":
        properties = ExtendedProperties(
            name=str(self.primary),
            secondary=self.secondary,
            displayname=str(self.primary),
        )
        return RandomDataNode(
            kinds=["RandomDataNode"],
            properties=properties,
        )

    @property
    def edges(self) -> Iterator[Edge]:
        for index in range(50):
            end = EdgePath(value="abc", match_by="id")
            start = EdgePath(value="abc", match_by="id")
            yield Edge.model_construct(start=start, end=end, kind="KnowsPerson")

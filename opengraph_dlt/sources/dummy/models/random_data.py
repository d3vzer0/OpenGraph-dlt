from collections.abc import Iterator
from pydantic import BaseModel, SkipValidation

from opengraph_dlt.sources.dummy.models.graph import (
    Node,
    NodeProperties,
    BaseResource,
)

# from opengraph_dlt.sources.shared.models.entries import Edge, EdgePath, EdgeProperties
from opengraph_dlt.sources.shared.docs import graph_resource, NodeDef, EdgeDef
from typing_extensions import TypedDict
from dataclasses import dataclass


class ExtendedProperties(NodeProperties):
    secondary: float


class RandomDataNode(Node):
    properties: ExtendedProperties


class EdgePath(BaseModel):
    value: str
    match_by: str


class Edge(BaseModel):
    kind: str
    start: SkipValidation[EdgePath]
    end: SkipValidation[EdgePath]


# @dataclass
# class EdgePath:
#     value: str
#     match_by: str


# @dataclass
# class Edge:
#     kind: str
#     start: EdgePath
#     end: EdgePath


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

    # @property
    # def edges(self) -> Iterator[int]:
    #     for index in range(100):
    #         yield index

    @property
    def edges(self) -> Iterator[Edge]:
        for index in range(50):
            end = EdgePath.model_construct(value="abc", match_by="id")
            start = EdgePath.model_construct(value="abc", match_by="id")
            yield 1
            # yield Edge(start=start, end=end, kind="KnowsPerson")

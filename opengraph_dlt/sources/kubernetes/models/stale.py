from opengraph_dlt.sources.kubernetes.models.graph import Node, NodeProperties
from opengraph_dlt.sources.shared.models.entries import Edge, EdgePath
from pydantic import BaseModel


class SourceRef(BaseModel):
    uid: str


class StaleReference(BaseModel):
    name: str
    resource_type: str
    edge_type: str
    source_ref: SourceRef

    @property
    def as_node(self) -> "StaleNode":
        properties = ExtendedProperties(
            name=self.name,
            displayname=self.name,
            exists=False,
            source_ref=self.source_ref.uid,
            source_edge_type=self.edge_type,
            namespace=None,
            uid=None,
        )
        return StaleNode(kinds=[self.resource_type], properties=properties)


class ExtendedProperties(NodeProperties):
    source_ref: str
    source_edge_type: str


class StaleNode(Node):
    properties: ExtendedProperties

    @property
    def _source_refs(self):
        start_path = EdgePath(value=self.properties.source_ref, match_by="id")
        end_path = EdgePath(value=self.id, match_by="id")
        edge = Edge(
            kind=self.properties.source_edge_type,
            start=start_path,
            end=end_path,
            properties={"stale": True},
        )
        return edge

    @property
    def edges(self):
        return [self._source_refs]

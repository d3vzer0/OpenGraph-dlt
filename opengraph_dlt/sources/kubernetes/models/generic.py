from pydantic import BaseModel, ConfigDict, field_validator
from datetime import datetime
from opengraph_dlt.sources.kubernetes.models.graph import (
    Node,
    NodeProperties,
    BaseResource,
)
from opengraph_dlt.sources.shared.docs import graph_resource, NodeDef
import json


class Metadata(BaseModel):
    name: str
    uid: str | None = None
    namespace: str | None = None
    creation_timestamp: datetime | None = None
    labels: dict | None = None


class ExtendedProperties(NodeProperties):
    model_config = ConfigDict(extra="allow")
    uid: str | None
    kind: str


class GenericNode(Node):
    properties: ExtendedProperties


@graph_resource(
    node=NodeDef(kind="Kube{Kind}", description="Unmapped Kubernetes resource"),
    edges=[],
)
class Generic(BaseResource):
    metadata: Metadata
    kind: str

    @property
    def as_node(self) -> "GenericNode":
        properties = ExtendedProperties(
            name=self.metadata.name,
            displayname=self.metadata.name,
            namespace=self.metadata.namespace,
            uid=self.metadata.uid,
            kind=self.kind,
            cluster=self._cluster,
        )
        return GenericNode(kinds=[f"Kube{self.kind}"], properties=properties)

    @property
    def edges(self):
        return []

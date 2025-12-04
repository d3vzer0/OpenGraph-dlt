from collections.abc import Iterator

from pydantic import BaseModel, field_validator, ConfigDict, PrivateAttr
from datetime import datetime
from opengraph_dlt.sources.kubernetes.models.graph import (
    Node,
    NodeProperties,
    NodeTypes,
    KubernetesCollector,
    BaseResource,
)
from opengraph_dlt.sources.shared.models.entries import Edge, EdgePath
from opengraph_dlt.sources.kubernetes.models.pod import Container
import json
from opengraph_dlt.sources.shared.docs import graph_resource, NodeDef, EdgeDef


class OwnerReferences(BaseModel):
    api_version: str
    controller: bool
    kind: str
    name: str
    uid: str


class Metadata(BaseModel):
    name: str
    uid: str
    namespace: str
    creation_timestamp: datetime | None = None
    labels: dict | None = {}
    owner_references: list[OwnerReferences] | None = None

    @field_validator("labels", mode="before")
    def set_default_if_none(cls, v):
        return v if v is not None else {}


class ExtendedProperties(NodeProperties):
    model_config = ConfigDict(extra="allow")
    namespace: str


class ReplicaSetNode(Node):
    properties: ExtendedProperties


@graph_resource(
    node=NodeDef(kind=NodeTypes.KubeReplicaSet.value, description="ReplicaSet node"),
    edges=[
        EdgeDef(
            start=NodeTypes.KubeReplicaSet.value,
            end="Kube{Controller}",
            kind="KubeOwnedBy",
            description="",
        )
    ],
)
class ReplicaSet(BaseResource):
    kind: str | None = "ReplicaSet"
    metadata: Metadata

    @field_validator("kind", mode="before")
    def set_default_if_none(cls, v):
        return v if v is not None else "ReplicaSet"

    @field_validator("metadata", mode="before")
    @classmethod
    def parse_json_string(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v

    @property
    def as_node(self) -> "ReplicaSetNode":
        properties = ExtendedProperties(
            name=self.metadata.name,
            displayname=self.metadata.name,
            namespace=self.metadata.namespace,
            uid=self.metadata.uid,
            cluster=self._cluster,
        )
        node = ReplicaSetNode(kinds=["KubeReplicaSet"], properties=properties)
        return node

    @property
    def _owned_by(self) -> Iterator[Edge]:
        start_path = EdgePath(value=self.as_node.id, match_by="id")
        if self.metadata.owner_references:
            for owner in self.metadata.owner_references:
                end_path_id = KubernetesCollector.guid(
                    owner.name,
                    f"Kube{owner.kind}",
                    cluster=self._cluster,
                    namespace=self.metadata.namespace,
                )
                end_path = EdgePath(value=end_path_id, match_by="id")
                yield Edge(kind="KubeOwnedBy", start=start_path, end=end_path)

    @property
    def edges(self) -> Iterator[Edge]:
        yield from self._owned_by

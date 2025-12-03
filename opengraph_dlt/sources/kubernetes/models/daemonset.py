from pydantic import BaseModel, field_validator, ConfigDict
from datetime import datetime
from opengraph_dlt.sources.kubernetes.models.graph import (
    Node,
    NodeProperties,
    BaseResource,
)
from opengraph_dlt.sources.kubernetes.models.pod import Container
from opengraph_dlt.sources.shared.docs import graph_resource, NodeDef


class Metadata(BaseModel):
    name: str
    uid: str
    namespace: str
    creation_timestamp: datetime | None = None
    labels: dict | None = {}

    @field_validator("labels", mode="before")
    def set_default_if_none(cls, v):
        return v if v is not None else {}


class HostPath(BaseModel):
    path: str


class Volume(BaseModel):
    name: str
    hostPath: HostPath | None = None


class TemplateSpec(BaseModel):
    containers: list[Container] | None = None
    volumes: list[Volume] | None = None


class Template(BaseModel):
    # metadata: Metadata
    spec: TemplateSpec


class Spec(BaseModel):
    template: Template


class ExtendedProperties(NodeProperties):
    model_config = ConfigDict(extra="allow")


class DaemonSetNode(Node):
    properties: ExtendedProperties


@graph_resource(node=NodeDef(kind="KubeDaemonSet", description="Kube DaemonSet"))
class DaemonSet(BaseResource):
    kind: str | None = "DaemonSet"
    metadata: Metadata
    creation_timestamp: datetime | None = None
    spec: Spec

    @field_validator("kind", mode="before")
    def set_default_if_none(cls, v):
        return v if v is not None else "DaemonSet"

    @property
    def as_node(self) -> "DaemonSetNode":
        properties = ExtendedProperties(
            name=self.metadata.name,
            displayname=self.metadata.name,
            namespace=self.metadata.namespace,
            uid=self.metadata.uid,
            cluster=self._cluster,
        )
        return DaemonSetNode(kinds=["KubeDaemonSet"], properties=properties)

    @property
    def edges(self):
        return []

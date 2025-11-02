from pydantic import BaseModel, field_validator, ConfigDict
from datetime import datetime
from sources.kubernetes.models.graph import Node, NodeProperties, NodeTypes, gen_guid
from sources.shared.models.entries import Edge, EdgePath
from sources.kubernetes.models.pod import Container


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


class StatefulSet(BaseModel):
    kind: str | None = "StatefulSet"
    metadata: Metadata
    spec: Spec

    @field_validator("kind", mode="before")
    def set_default_if_none(cls, v):
        return v if v is not None else "StatefulSet"


class ExtendedProperties(NodeProperties):
    model_config = ConfigDict(extra="allow")


class StatefulSetNode(Node):
    properties: ExtendedProperties

    @property
    def edges(self):
        return []

    @classmethod
    def from_input(cls, **kwargs) -> "StatefulSetNode":
        model = StatefulSet(**kwargs)
        properties = ExtendedProperties(
            name=model.metadata.name,
            displayname=model.metadata.name,
            namespace=model.metadata.namespace,
            uid=model.metadata.uid,
        )
        node = cls(kinds=["KubeStatefulSet"], properties=properties)
        return node

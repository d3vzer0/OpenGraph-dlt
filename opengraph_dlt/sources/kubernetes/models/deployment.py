from pydantic import BaseModel, field_validator, ConfigDict
from datetime import datetime
from opengraph_dlt.sources.kubernetes.models.graph import Node, NodeProperties
from opengraph_dlt.sources.kubernetes.models.pod import Container
import json


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
    host_path: HostPath | None = None


class TemplateSpec(BaseModel):
    containers: list[Container] | None = None
    volumes: list[Volume] | None = None


class Template(BaseModel):
    # metadata: Metadata
    spec: TemplateSpec


class Spec(BaseModel):
    template: Template


class Deployment(BaseModel):
    kind: str | None = "Deployment"
    metadata: Metadata
    spec: Spec

    @field_validator("kind", mode="before")
    def set_default_if_none(cls, v):
        return v if v is not None else "Deployment"

    @field_validator("metadata", "spec", mode="before")
    @classmethod
    def parse_json_string(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v


class ExtendedProperties(NodeProperties):
    model_config = ConfigDict(extra="allow")
    namespace: str


class DeploymentNode(Node):
    properties: ExtendedProperties

    # @property
    # def _volume_edges(self):
    #     print()

    @property
    def edges(self):
        return []

    @classmethod
    def from_input(cls, **kwargs) -> "DeploymentNode":
        model = Deployment(**kwargs)
        properties = ExtendedProperties(
            name=model.metadata.name,
            displayname=model.metadata.name,
            namespace=model.metadata.namespace,
            uid=model.metadata.uid,
        )
        node = cls(kinds=["KubeDeployment"], properties=properties)
        return node

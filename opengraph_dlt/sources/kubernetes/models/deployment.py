from pydantic import BaseModel, field_validator, ConfigDict
from datetime import datetime
from opengraph_dlt.sources.kubernetes.models.graph import (
    Node,
    NodeProperties,
    BaseResource,
)
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


class ExtendedProperties(NodeProperties):
    model_config = ConfigDict(extra="allow")
    namespace: str


class DeploymentNode(Node):
    properties: ExtendedProperties


class Deployment(BaseResource):
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

    @property
    def as_node(self) -> "DeploymentNode":
        properties = ExtendedProperties(
            name=self.metadata.name,
            displayname=self.metadata.name,
            namespace=self.metadata.namespace,
            uid=self.metadata.uid,
        )
        return DeploymentNode(kinds=["KubeDeployment"], properties=properties)

    @property
    def edges(self):
        return []

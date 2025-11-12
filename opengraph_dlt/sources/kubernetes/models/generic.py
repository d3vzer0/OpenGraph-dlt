from pydantic import BaseModel, ConfigDict, field_validator
from datetime import datetime
from sources.kubernetes.models.graph import Node, NodeProperties
import json


class Metadata(BaseModel):
    name: str
    uid: str | None = None
    namespace: str | None = None
    creation_timestamp: datetime | None = None
    labels: dict | None = None


class Generic(BaseModel):
    metadata: Metadata
    kind: str

    @field_validator("metadata", mode="before")
    @classmethod
    def parse_json_string(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v


class ExtendedProperties(NodeProperties):
    model_config = ConfigDict(extra="allow")
    uid: str | None
    kind: str


class GenericNode(Node):
    properties: ExtendedProperties

    @property
    def edges(self):
        return []

    @classmethod
    def from_input(cls, **kwargs) -> "GenericNode":
        model = Generic(**kwargs)
        properties = ExtendedProperties(
            name=model.metadata.name,
            displayname=model.metadata.name,
            namespace=model.metadata.namespace,
            uid=model.metadata.uid,
            kind=model.kind,
        )
        return cls(kinds=[f"Kube{model.kind}"], properties=properties)

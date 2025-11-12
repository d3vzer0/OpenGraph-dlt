from pydantic import BaseModel, field_validator, Field
from datetime import datetime
from opengraph_dlt.sources.kubernetes.models.graph import (
    Node,
    NodeProperties,
    NodeTypes,
    KubernetesCollector,
)
from opengraph_dlt.sources.shared.models.entries import Edge, EdgePath, EdgeProperties
from typing import Optional, Any
from enum import Enum
import fnmatch
import json


class Verbs(str, Enum):
    get = "get"
    list = "list"
    watch = "watch"
    create = "create"
    update = "update"
    patch = "patch"
    delete = "delete"
    deletecollection = "deletecollection"
    proxy = "proxy"
    wildcard = "*"
    impersonate = "impersonate"

    def __str__(self):
        return self.value


VERB_TO_PERMISSION = {
    "get": "KubeCanGet",
    "list": "KubeCanList",
    "watch": "KubeCanWatch",
    "create": "KubeCanCreate",
    "update": "KubeCanUpdate",
    "patch": "KubeCanPatch",
    "delete": "KubeCanDelete",
    "deletecollection": "KubeCanDeleteCollection",
    "proxy": "KubeCanProxy",
    "*": "KubeCanAll",
}


class Spec(BaseModel):
    node_name: str


class Metadata(BaseModel):
    name: str
    uid: str
    namespace: str
    creation_timestamp: datetime | None = None
    labels: dict | None = None


class Rule(BaseModel):
    api_groups: list[str] = ["__core__"]
    resources: list[str]
    verbs: list[Verbs]
    resource_names: Optional[list[str]] = None

    @field_validator("api_groups")
    def validate_api_groups(cls, v):
        if not v or (len(v) == 1 and v[0] == ""):
            return ["__core__"]
        return v


class Role(BaseModel):
    metadata: Metadata
    rules: Optional[list[Rule]] = []
    kind: str | None = "Role"

    @field_validator("kind", mode="before")
    def set_default_if_none(cls, v):
        return v if v is not None else "Role"

    @field_validator("rules", mode="before")
    @classmethod
    def parse_rules(cls, value: Any):
        if isinstance(value, str):
            value = json.loads(value)
        return value or []

    @field_validator("metadata", mode="before")
    @classmethod
    def parse_json_string(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v


class ExtendedProperties(NodeProperties):
    # namespace: str
    rules: list[Rule] = Field(exclude=True)

    @field_validator("rules")
    def validate_rules(cls, v):
        if not v:
            return []
        return v


class RoleNode(Node):
    properties: ExtendedProperties

    def _matching_verbs(self, verbs: list) -> list:
        matched = []
        for verb in verbs:
            for key in VERB_TO_PERMISSION.keys():
                if fnmatch.fnmatch(key, verb.value) and key != "*":
                    matched.append(key)
        return matched

    @property
    def _namespace_edge(self):
        target_id = KubernetesCollector.guid(
            self.properties.namespace, NodeTypes.KubeNamespace, self._cluster
        )
        start_path = EdgePath(value=self.id, match_by="id")
        end_path = EdgePath(value=target_id, match_by="id")
        edge = Edge(kind="KubeBelongsTo", start=start_path, end=end_path)
        return edge

    def _rule_edge(self, rule: Rule):
        if not rule.api_groups or not rule.resources:
            return []

        start_path = EdgePath(value=self.id, match_by="id")
        matched_verbs = self._matching_verbs(rule.verbs)
        namespace = self.properties.namespace

        all_allowed_resources = []
        for resource in rule.resources:
            allowed_resources = self._lookup.allowed_namespaced_resources(
                resource, namespace
            )
            all_allowed_resources.extend(allowed_resources)

        targets = []
        for name, kind, r_namespace, singular, rd in all_allowed_resources:
            targets.append(
                Edge(
                    kind="KubeHasPermissions",
                    start=start_path,
                    end=EdgePath(
                        value=KubernetesCollector.guid(
                            name, f"Kube{kind}", self._cluster, namespace
                        ),
                        match_by="id",
                    ),
                    properties=EdgeProperties(verbs=matched_verbs),
                )
            )

        return targets

    @property
    def _rules_edge(self):
        edges = []
        for rule in self.properties.rules:
            edges.extend(self._rule_edge(rule))
        return edges

    @property
    def edges(self):
        return [self._namespace_edge, *self._rules_edge]

    @classmethod
    def from_input(cls, **kwargs) -> "RoleNode":
        model = Role(**kwargs)
        properties = ExtendedProperties(
            rules=model.rules,
            name=model.metadata.name,
            displayname=model.metadata.name,
            namespace=model.metadata.namespace,
            uid=model.metadata.uid,
        )
        return cls(
            kinds=["KubeScopedRole", "KubeRole"],
            properties=properties,
        )

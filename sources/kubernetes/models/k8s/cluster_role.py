from pydantic import BaseModel, field_validator, Field
from datetime import datetime
from ..entries import Node, NodeProperties, Edge, EdgePath
from typing import Optional, Any
from enum import Enum
from sources.kubernetes.utils.guid import get_guid, NodeTypes, get_generic_guid
import fnmatch
from .cluster import Cluster
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
    impersonate = "impersonate"
    wildcard = "*"
    approve = "approve"
    sign = "sign"
    escalate = "escalate"
    bind = "bind"

    def __str__(self):
        return self.value


VERB_TO_PERMISSION = {
    "get": "K8sCanGet",
    "list": "K8sCanList",
    "watch": "K8sCanWatch",
    "create": "K8sCanCreate",
    "update": "K8sCanUpdate",
    "patch": "K8sCanPatch",
    "delete": "K8sCanDelete",
    "deletecollection": "K8sCanDeleteCollection",
    "proxy": "K8sCanProxy",
    "impersonate": "K8sCanImpersonate",
    "approve": "K8sCanApprove",
    "sign": "K8sCanSign",
    "escalate": "K8sCanEscalate",
    "bind": "K8sCanBind",
    "*": "K8sCanAll",
}


class Metadata(BaseModel):
    name: str
    uid: str
    creation_timestamp: datetime
    namespace: str | None = ""
    labels: dict | None = None


class Rule(BaseModel):
    api_groups: Optional[list[str]] = ["__core__"]
    resources: Optional[list[str]] = []
    verbs: list[Verbs]
    resource_names: Optional[list[str]] = None

    @field_validator("api_groups")
    def validate_api_groups(cls, v):
        if not v or (len(v) == 1 and v[0] == ""):
            return ["__core__"]
        return v


class ClusterRole(BaseModel):
    metadata: Metadata
    rules: list[Rule] = []
    kind: str | None = "ClusterRole"

    @field_validator("kind", mode="before")
    def set_default_if_none(cls, v):
        return v if v is not None else "ClusterRole"

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
    rules: list[Rule] = Field(exclude=True)

    @field_validator("rules")
    def validate_rules(cls, v):
        if not v:
            return []
        return v


class ClusterRoleNode(Node):
    properties: ExtendedProperties

    @property
    def _cluster_edge(self):
        start_path = EdgePath(value=self.id, match_by="id")
        cluster = Cluster(name=self._cluster)
        end_path = EdgePath(value=cluster.uid, match_by="id")
        edge = Edge(kind="K8sBelongsTo", start=start_path, end=end_path)
        return edge

    def _matching_verbs(self, verbs: list) -> list:
        matched = []
        for verb in verbs:
            for key in VERB_TO_PERMISSION.keys():
                if fnmatch.fnmatch(key, verb.value) and key != "*":
                    matched.append(key)
        return matched

    def _rule_edge(self, rule: Rule):
        if not rule.api_groups or not rule.resources:
            return []

        start_path = EdgePath(value=self.id, match_by="id")
        matched_verbs = self._matching_verbs(rule.verbs)

        all_allowed_resources = []
        for resource in rule.resources:
            allowed_resources = self._lookup.allowed_system_resources(resource)
            all_allowed_resources.extend(allowed_resources)

        targets = []
        for name, kind, singular, rd in all_allowed_resources:
            targets.append(
                Edge(
                    kind="K8sHasPermissions",
                    start=start_path,
                    end=EdgePath(
                        value=get_generic_guid(name, f"K8s{kind}", self._cluster),
                        match_by="id",
                    ),
                    properties={"verbs": matched_verbs},
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
        return [self._cluster_edge, *self._rules_edge]

    @classmethod
    def from_input(cls, **kwargs) -> "ClusterRoleNode":
        model = ClusterRole(**kwargs)
        properties = ExtendedProperties(
            name=model.metadata.name,
            displayname=model.metadata.name,
            rules=model.rules,
            uid=model.metadata.uid,
            namespace=None,
        )
        return cls(
            kinds=["K8sClusterRole", "K8sRole"],
            properties=properties,
        )


# class ClusterRoleGraphEntries(GraphEntries):
#     nodes: list[ClusterRoleNode] = []

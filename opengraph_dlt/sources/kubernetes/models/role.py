from collections.abc import Iterator

from pydantic import BaseModel, field_validator, Field
from datetime import datetime
from opengraph_dlt.sources.kubernetes.models.graph import (
    Node,
    NodeProperties,
    NodeTypes,
    KubernetesCollector,
    BaseResource,
)
from opengraph_dlt.sources.shared.models.entries import Edge, EdgePath, EdgeProperties
from typing import Optional, Any
from enum import Enum
import fnmatch
import json
from opengraph_dlt.sources.shared.docs import graph_resource, NodeDef, EdgeDef


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
    approve = "approve"
    sign = "sign"
    escalate = "escalate"
    bind = "bind"
    use = "use"

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
    "impersonate": "KubeCanImpersonate",
    "approve": "KubeCanApprove",
    "sign": "KubeCanSign",
    "escalate": "KubeCanEscalate",
    "bind": "KubeCanBind",
    "*": "KubeCanAll",
    "use": "KubeCanUse",
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


class ExtendedProperties(NodeProperties):
    namespace: str
    rules: list[Rule] = Field(exclude=True)

    @field_validator("rules")
    def validate_rules(cls, v):
        if not v:
            return []
        return v


class RoleNode(Node):
    properties: ExtendedProperties


@graph_resource(
    node=NodeDef(kind=NodeTypes.KubeScopedRole.value, description="Namespaced role"),
    edges=[
        EdgeDef(
            start=NodeTypes.KubeScopedRole.value,
            end=NodeTypes.KubeNamespace.value,
            kind="KubeBelongsTo",
            description="Role belongs to a namespace",
        ),
        EdgeDef(
            start=NodeTypes.KubeScopedRole.value,
            end="Kube{Resource}",
            kind="KubeHasPermissions",
            description="Role grants permissions to namespaced resources",
        ),
    ],
)
class Role(BaseResource):
    metadata: Metadata
    rules: Optional[list[Rule]] = []
    kind: str | None = "Role"

    @field_validator("kind", mode="before")
    def set_default_if_none(cls, v):
        return v if v is not None else "Role"

    @property
    def as_node(self) -> "RoleNode":
        properties = ExtendedProperties(
            rules=self.rules,
            name=self.metadata.name,
            displayname=self.metadata.name,
            namespace=self.metadata.namespace,
            uid=self.metadata.uid,
            cluster=self._cluster,
        )
        return RoleNode(
            kinds=["KubeScopedRole", "KubeRole"],
            properties=properties,
        )

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
            self.metadata.namespace, NodeTypes.KubeNamespace, self._cluster
        )
        start_path = EdgePath(value=self.as_node.id, match_by="id")
        end_path = EdgePath(value=target_id, match_by="id")
        edge = Edge(kind="KubeBelongsTo", start=start_path, end=end_path)
        return edge

    def _rule_edge(self, rule: Rule) -> Iterator[Edge]:
        if not rule.api_groups or not rule.resources:
            return

        start_path = EdgePath(value=self.as_node.id, match_by="id")
        matched_verbs = self._matching_verbs(rule.verbs)
        namespace = self.metadata.namespace
        for resource in rule.resources:
            allowed_resources = self._lookup.allowed_namespaced_resources(
                resource, namespace
            )
            for name, kind, r_namespace, singular, rd in allowed_resources:
                yield Edge(
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

    @property
    def _rules_edge(self) -> Iterator[Edge]:
        for rule in self.rules:
            yield from self._rule_edge(rule)

    @property
    def edges(self) -> Iterator[Edge]:
        yield self._namespace_edge
        yield from self._rules_edge

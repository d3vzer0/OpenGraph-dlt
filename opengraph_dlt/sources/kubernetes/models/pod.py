from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    BeforeValidator,
    field_validator,
    PrivateAttr,
)
from datetime import datetime
from pydantic_core import PydanticUseDefault
from opengraph_dlt.sources.kubernetes.models.graph import (
    Node,
    NodeProperties,
    Edge,
    NodeTypes,
    KubernetesCollector,
    BaseResource,
)
from opengraph_dlt.sources.shared.models.entries import EdgePath
from typing import Optional, Any, TypeVar, Annotated
from opengraph_dlt.sources.kubernetes.models.volume import Volume as HostVolume
from opengraph_dlt.sources.shared.docs import graph_resource, NodeDef, EdgeDef
from collections.abc import Iterator


def default_if_none(value: Any) -> Any:
    if value is None:
        raise PydanticUseDefault()
    return value


T = TypeVar("T")
DefaultIfNone = Annotated[T, BeforeValidator(default_if_none)]


class SecurityContext(BaseModel):
    allow_privilege_escalation: DefaultIfNone[bool | None] = False
    privileged: DefaultIfNone[bool | None] = False


class VolumeMount(BaseModel):
    mount_path: str
    name: str


class HostPath(BaseModel):
    path: str


class Volume(BaseModel):
    name: str
    host_path: HostPath | None = None


class Container(BaseModel):
    image: str
    security_context: DefaultIfNone[SecurityContext | None] = Field(
        default_factory=SecurityContext
    )
    volume_mounts: list[VolumeMount] | None = []


class Spec(BaseModel):
    node_name: str | None = None
    service_account_name: Optional[str] = "default"
    containers: list[Container]
    volumes: DefaultIfNone[list[Volume] | None] = Field(default=[])


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
    resource_version: str
    labels: dict | None = {}
    owner_references: list[OwnerReferences] | None = None

    @field_validator("labels", mode="before")
    def set_default_if_none(cls, v):
        return v if v is not None else {}


class ExtendedProperties(NodeProperties):
    model_config = ConfigDict(extra="allow")
    namespace: str
    node_name: str | None = None
    service_account_name: str
    labels: list[str] | None = None


class PodNode(Node):
    properties: ExtendedProperties


@graph_resource(
    node=NodeDef(kind=NodeTypes.KubePod.value, description="Kubernetes pod node"),
    edges=[
        EdgeDef(
            start=NodeTypes.KubePod.value,
            end=NodeTypes.KubeNode.value,
            kind="KubeRunsOn",
            description="Pod is running on a node",
        ),
        EdgeDef(
            start=NodeTypes.KubePod.value,
            end=NodeTypes.KubeNamespace.value,
            kind="KubeBelongsTo",
            description="Pod belongs to a namespace",
        ),
        EdgeDef(
            start=NodeTypes.KubePod.value,
            end=NodeTypes.KubeServiceAccount.value,
            kind="KubeRunsAs",
            description="Pod runs as the service account",
        ),
        EdgeDef(
            start=NodeTypes.KubePod.value,
            end="Kube{Controller}",
            kind="KubeOwnedBy",
            description="Pod is part of a ReplicaSet/StatefulSet/DaemonSet/etc",
        ),
        EdgeDef(
            start=NodeTypes.KubePod.value,
            end=NodeTypes.KubeVolume.value,
            kind="KubeAttaches",
            description="Pod attaches HostPath volumes",
        ),
    ],
)
class Pod(BaseResource):
    metadata: Metadata
    spec: Spec
    kind: str | None = "Pod"

    @field_validator("kind", mode="before")
    def set_default_if_none(cls, v):
        return v if v is not None else "Pod"

    @property
    def as_node(self) -> "PodNode":
        if "name" in self.metadata.labels:
            del self.metadata.labels["name"]

        properties = ExtendedProperties(
            name=self.metadata.name,
            displayname=self.metadata.name,
            namespace=self.metadata.namespace,
            node_name=self.spec.node_name,
            uid=self.metadata.uid,
            service_account_name=self.spec.service_account_name,
            cluster=self._cluster,
            **self.metadata.labels,
            **self.spec.containers[0].security_context.model_dump(),
        )
        node = PodNode(kinds=["KubePod"], properties=properties)
        return node

    @property
    def _namespace_edge(self) -> "Edge":
        target_id = KubernetesCollector.guid(
            self.metadata.namespace, NodeTypes.KubeNamespace, self._cluster
        )
        start_path = EdgePath(value=self.as_node.id, match_by="id")
        end_path = EdgePath(value=target_id, match_by="id")
        edge = Edge(kind="KubeBelongsTo", start=start_path, end=end_path)
        return edge

    @property
    def _node_edge(self) -> "Edge":
        if self.spec.node_name:
            target_id = KubernetesCollector.guid(
                self.spec.node_name, NodeTypes.KubeNode, self._cluster
            )
            start_path = EdgePath(value=self.as_node.id, match_by="id")
            end_path = EdgePath(value=target_id, match_by="id")
            edge = Edge(kind="KubeRunsOn", start=start_path, end=end_path)
            return edge

    @property
    def _service_account_edge(self) -> "Edge":
        target_id = KubernetesCollector.guid(
            self.spec.service_account_name,
            NodeTypes.KubeServiceAccount,
            self._cluster,
            namespace=self.metadata.namespace,
        )
        start_path = EdgePath(value=self.as_node.id, match_by="id")
        end_path = EdgePath(value=target_id, match_by="id")
        edge = Edge(kind="KubeRunsAs", start=start_path, end=end_path)
        return edge

    @property
    def _owned_by(self) -> "Iterator[Edge]":
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
    def _volume_edges(self) -> "Iterator[Edge]":
        start_path = EdgePath(value=self.as_node.id, match_by="id")
        for volume in self.spec.volumes:
            if volume.host_path:
                node_name = self.spec.node_name
                if not node_name:
                    continue
                volume_object = HostVolume(
                    node_name=node_name, path=volume.host_path.path
                )
                end_path_id = KubernetesCollector.guid(
                    volume_object.name, NodeTypes.KubeVolume, self._cluster
                )
                end_path = EdgePath(value=end_path_id, match_by="id")
                yield Edge(
                    kind="KubeAttaches",
                    start=start_path,
                    end=end_path,
                    properties={"name": volume.name, "type": "HostPath"},
                )

    @property
    def edges(self) -> "Iterator[Edge]":
        yield self._node_edge
        yield self._namespace_edge
        yield self._service_account_edge
        yield from self._owned_by
        yield from self._volume_edges

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, computed_field
from opengraph_dlt.sources.shared.models.graph import MetaData, Graph as CommonGraph
from abc import ABC
from enum import Enum
from datetime import datetime
from typing import Optional, ClassVar
from opengraph_dlt.sources.kubernetes.lookup import KubernetesLookup
from opengraph_dlt.sources.shared.models.entries import Node as BaseNode, Edge
from opengraph_dlt.sources.shared.guid import Collector

# from opengraph_dlt.sources.shared.models.examples import NodeExample
import importlib
import uuid


class NodeTypes(str, Enum):
    KubeCluster = "KubeCluster"
    KubeNamespace = "KubeNamespace"
    KubeScopedRole = "KubeScopedRole"
    KubeScopedRoleBinding = "KubeScopedRoleBinding"
    KubeNode = "KubeNode"
    KubePod = "KubePod"
    KubeServiceAccount = "KubeServiceAccount"
    KubeClusterRole = "KubeClusterRole"
    KubeClusterRoleBinding = "KubeClusterRoleBinding"
    KubeResource = "KubeResource"
    KubeResourceGroup = "KubeResourceGroup"
    KubeUser = "KubeUser"
    KubeGroup = "KubeGroup"
    KubeReplicaSet = "KubeReplicaSet"
    KubeStatefulSet = "KubeStatefulSet"
    KubeDeployment = "KubeDeployment"
    KubeDaemonSet = "KubeDaemonSet"
    KubeVolume = "KubeVolume"


class KubernetesCollector(Collector):

    @staticmethod
    def guid(
        name: str,
        resource_type: NodeTypes | str,
        cluster: str,
        namespace: str = "__global__",
    ):
        type_value = (
            resource_type.value
            if isinstance(resource_type, NodeTypes)
            else resource_type
        )
        uuid_namespace = uuid.NAMESPACE_DNS
        resource_path = f"{name}.{type_value}.{namespace}.{cluster}"
        return str(uuid.uuid5(uuid_namespace, resource_path))


# def KubernetesCollector.guid(
#     name: str,
#     resource_type: NodeTypes | str,
#     cluster: str,
#     namespace: str = "__global__",
# ) -> str:
#     type_value = (
#         resource_type.value if isinstance(resource_type, NodeTypes) else resource_type
#     )
#     uuid_namespace = uuid.NAMESPACE_DNS
#     resource_path = f"{name}.{type_value}.{namespace}.{cluster}"
#     return str(uuid.uuid5(uuid_namespace, resource_path))


class NodeProperties(BaseModel):
    model_config = ConfigDict(extra="allow")
    name: str
    displayname: str
    namespace: str | None
    last_seen: datetime = Field(default_factory=datetime.now)
    uid: str | None


class Node(BaseNode, ABC):
    properties: NodeProperties
    _lookup: KubernetesLookup = PrivateAttr()
    _cluster: str = PrivateAttr()
    _scope: Optional[str] = PrivateAttr(default=None)

    @computed_field
    @property
    def id(self) -> str:
        scope = (
            "__global__" if not self.properties.namespace else self.properties.namespace
        )

        kind = self.kinds[0]
        resource_type = NodeTypes[kind] if kind in NodeTypes else kind
        dyn_uid = KubernetesCollector.guid(
            self.properties.name, resource_type, self._cluster, scope
        )
        return dyn_uid


class GraphEntries(BaseModel):
    nodes: list[Node] = []
    edges: list[Edge] = Field(default_factory=list)


class Graph(CommonGraph):
    graph: GraphEntries
    metadata: MetaData = Field(default_factory=MetaData)

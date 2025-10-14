import uuid
from enum import Enum


# from sources.kubernetes.utils.guid import NodeTypes
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


def get_guid(
    name: str, resource_type: NodeTypes, cluster: str, namespace: str = "__global__"
) -> str:
    uuid_namespace = uuid.NAMESPACE_DNS
    resource_path = f"{name}.{resource_type.value}.{namespace}.{cluster}"
    return str(uuid.uuid5(uuid_namespace, resource_path))


def get_generic_guid(
    name: str, resource_type: str, cluster: str, namespace: str = "__global__"
) -> str:
    uuid_namespace = uuid.NAMESPACE_DNS
    resource_path = f"{name}.{resource_type}.{namespace}.{cluster}"
    return str(uuid.uuid5(uuid_namespace, resource_path))

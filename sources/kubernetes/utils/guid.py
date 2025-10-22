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
    name: str,
    resource_type: NodeTypes | str,
    cluster: str,
    namespace: str = "__global__",
) -> str:
    type_value = (
        resource_type.value if isinstance(resource_type, NodeTypes) else resource_type
    )
    uuid_namespace = uuid.NAMESPACE_DNS
    resource_path = f"{name}.{type_value}.{namespace}.{cluster}"
    return str(uuid.uuid5(uuid_namespace, resource_path))

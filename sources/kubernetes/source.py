from kubernetes import client, config
from kubernetes.dynamic import DynamicClient
from sources.kubernetes.utils.lookup import LookupManager
from .models.pod import Pod, PodNode, Volume as PodVolume
from .models.volume import Volume, VolumeNode
from .models.namespace import Namespace, NamespaceNode
from .models.daemonset import DaemonSet, DaemonSetNode
from .models.replicaset import ReplicaSet, ReplicaSetNode
from .models.statefulset import StatefulSet, StatefulSetNode
from .models.deployment import Deployment, DeploymentNode
from .models.resource_group import ResourceGroup, ResourceGroupNode
from .models.generic import Generic, GenericNode
from .models.node import Node as KubeNode, NodeOutput
from .models.role import Role, RoleNode
from .models.role_binding import RoleBinding, RoleBindingNode
from .models.cluster_role import ClusterRole, ClusterRoleNode
from .models.cluster_role_binding import ClusterRoleBinding, ClusterRoleBindingNode
from .models.service_account import ServiceAccount, ServiceAccountNode
from .models.resource import Resource, ResourceNode
from .models.graph import Node as GraphNode, Graph, GraphEntries
from .models.identities import User, UserNode, Group, GroupNode
from .models.eks.eks_cluster_role import EKSVirtualClusterAdminRole, Metadata

from functools import wraps
from dlt.sources.filesystem import filesystem as filesystemsource, read_jsonl, readers


import dlt
from typing import Type, TypeVar

T = TypeVar("T", bound=GraphNode)
E = TypeVar("E", bound=GraphEntries)

IDENTITY_MAPPING = {"User": User, "Group": Group}
RESOURCE_TYPES = {
    "Pod": Pod,
    "ServiceAccount": ServiceAccount,
    "Role": Role,
    "Node": KubeNode,
    "Namespace": Namespace,
    "RoleBinding": RoleBinding,
    "ClusterRole": ClusterRole,
    "ClusterRoleBinding": ClusterRoleBinding,
    "ReplicaSet": ReplicaSet,
    "DaemonSet": DaemonSet,
    "StatefulSet": StatefulSet,
    "Deployment": Deployment,
    # "Service": ServiceNode
}


@dlt.source()
def kubernetes_resources(
    kube_config: None | str = None, cluster: str = dlt.config.value
):

    config.load_kube_config(kube_config)
    api_client = client.ApiClient()
    dyn_client = DynamicClient(api_client)

    @dlt.resource(columns=KubeNode, table_name="nodes", parallelized=True)
    def nodes():
        v1 = client.CoreV1Api()
        nodes = v1.list_node()
        for node in nodes.items:
            yield node.to_dict()

    @dlt.resource(columns=Namespace, table_name="namespaces", parallelized=True)
    def namespaces():
        v1 = client.CoreV1Api()
        namespaces = v1.list_namespace()
        for ns in namespaces.items:
            yield ns.to_dict()

    @dlt.resource(columns=DaemonSet, table_name="daemonsets", parallelized=True)
    def daemonsets():
        v1 = client.AppsV1Api()
        daemonsets = v1.list_daemon_set_for_all_namespaces()
        for daemonset in daemonsets.items:
            yield daemonset.to_dict()

    @dlt.resource(columns=StatefulSet, table_name="statefulsets", parallelized=True)
    def statefulsets():
        v1 = client.AppsV1Api()
        statefulsets = v1.list_stateful_set_for_all_namespaces()
        for replica in statefulsets.items:
            yield replica.to_dict()

    @dlt.resource(columns=ReplicaSet, table_name="replicasets", parallelized=True)
    def replicasets():
        v1 = client.AppsV1Api()
        replicasets = v1.list_replica_set_for_all_namespaces()
        for replica in replicasets.items:
            yield replica.to_dict()

    @dlt.resource(columns=Deployment, table_name="deployments", parallelized=True)
    def deployments():
        v1 = client.AppsV1Api()
        deployments = v1.list_deployment_for_all_namespaces()
        for deployment in deployments.items:
            yield deployment.to_dict()

    @dlt.resource(columns=Pod, table_name="pods", parallelized=True)
    def pods(incremental=dlt.sources.incremental("metadata.resource_version")):
        v1 = client.CoreV1Api()
        pods = v1.list_pod_for_all_namespaces()
        for pod in pods.items:
            yield pod.to_dict()

    @dlt.transformer(data_from=pods, columns=Volume, table_name="cust_volumes")
    def volumes(pod: dict):
        volumes = pod["spec"]["volumes"]
        if volumes:
            node_name = pod["spec"]["node_name"]
            for volume in volumes:
                if not volume["host_path"]:
                    continue
                yield {"node_name": node_name, "path": volume["host_path"]["path"]}

    @dlt.resource(columns=Role, table_name="roles", parallelized=True)
    def roles():
        v1 = client.RbacAuthorizationV1Api()
        roles = v1.list_role_for_all_namespaces()
        for role in roles.items:
            yield role.to_dict()

    @dlt.resource(columns=RoleBinding, table_name="role_bindings", parallelized=True)
    def role_bindings():
        v1 = client.RbacAuthorizationV1Api()
        rolebs = v1.list_role_binding_for_all_namespaces()
        for roleb in rolebs.items:
            yield roleb.to_dict()

    @dlt.transformer(data_from=role_bindings, table_name="cust_users", columns=User)
    def users_role(role_binding):
        for subject in role_binding["subjects"]:
            if subject["kind"] == "User":
                yield subject

    @dlt.transformer(data_from=role_bindings, table_name="cust_groups", columns=Group)
    def groups_role(role_binding):
        for subject in role_binding["subjects"]:
            if subject["kind"] == "Group":
                yield subject

    @dlt.resource(columns=ClusterRole, table_name="cluster_roles", parallelized=True)
    def cluster_roles():
        v1 = client.RbacAuthorizationV1Api()
        roles = v1.list_cluster_role()
        for role in roles.items:
            yield role.to_dict()

    @dlt.resource(
        columns=ClusterRoleBinding,
        table_name="cluster_role_bindings",
        parallelized=True,
    )
    def cluster_role_bindings():
        v1 = client.RbacAuthorizationV1Api()
        rolebs = v1.list_cluster_role_binding()
        for roleb in rolebs.items:
            yield roleb.to_dict()

    @dlt.transformer(
        data_from=cluster_role_bindings, table_name="cust_users", columns=User
    )
    def users_cluster_role(role_binding):
        for subject in role_binding["subjects"]:
            if subject["kind"] == "User":
                yield subject

    @dlt.transformer(
        data_from=cluster_role_bindings, table_name="cust_groups", columns=Group
    )
    def groups_cluster_role(role_binding):
        for subject in role_binding["subjects"]:
            if subject["kind"] == "Group":
                yield subject

    @dlt.resource(
        columns=ServiceAccount, table_name="service_accounts", parallelized=True
    )
    def service_accounts():
        v1 = client.CoreV1Api()
        service_accounts = v1.list_service_account_for_all_namespaces()
        for service_account in service_accounts.items:
            yield service_account.to_dict()

    @dlt.resource(
        columns=Resource, table_name="resource_definitions", parallelized=True
    )
    def resource_definitions():
        api_client = client.ApiClient()
        dyn_client = DynamicClient(api_client)
        discovered_resources = dyn_client.resources.search()
        for resource in discovered_resources:
            if not resource.kind.endswith("List"):
                yield resource.to_dict()

    @dlt.transformer(
        data_from=resource_definitions,
        table_name="cust_api_groups",
        columns=ResourceGroup,
    )
    def api_groups(item):
        if item["group"]:
            yield {"name": item["group"], "api_version": item["api_version"]}

    @dlt.transformer(
        data_from=resource_definitions,
        table_name="unmapped",
        columns=Generic,
        parallelized=True,
    )
    def unmapped_resources(resource: dict):
        resource_filter = (
            not resource["kind"] in RESOURCE_TYPES and "list" in resource["verbs"]
        )
        if resource_filter:
            resource_client = dyn_client.resources.get(
                api_version=resource["api_version"], kind=resource["kind"]
            )
            items = resource_client.get()
            for item in items.items:
                yield item.to_dict()

    return (
        pods,
        namespaces,
        nodes,
        service_accounts,
        deployments,
        replicasets,
        statefulsets,
        daemonsets,
        roles,
        role_bindings,
        cluster_roles,
        cluster_role_bindings,
        resource_definitions,
        api_groups,
        unmapped_resources,
        volumes,
        users_cluster_role,
        groups_cluster_role,
        users_role,
        groups_role,
    )


@dlt.source(name="kubernetes_opengraph")
def kubernetes_opengraph(
    *,
    cluster: str,
    lookup: LookupManager,
    bucket_url: str = dlt.config.value,
):

    def json_resource(subdir: str):
        files = filesystemsource(
            bucket_url=bucket_url,
            file_glob=f"{subdir}/**/*.jsonl.gz",
        )
        reader = (files | read_jsonl()).with_name(f"{subdir}_fs")
        return reader

    def build_graph(model_cls: Type[T], resource: dict) -> Graph:
        node = model_cls.from_input(**resource)
        node._cluster = cluster
        node._lookup = lookup

        entries = GraphEntries(
            nodes=[node],
            edges=[edge for edge in node.edges if edge],
        )
        return Graph(graph=entries)

    @dlt.transformer(data_from=json_resource("pods"), columns=Graph)
    def pods_graph(pods: list):
        for pod in pods:
            yield build_graph(PodNode, pod)

    @dlt.transformer(data_from=json_resource("cust_volumes"), columns=Graph)
    def volumes_graph(volumes: list):
        for volume in volumes:
            yield build_graph(VolumeNode, volume)

    @dlt.transformer(data_from=json_resource("namespaces"), columns=Graph)
    def namespaces_graph(namespaces):
        for namespace in namespaces:
            yield build_graph(NamespaceNode, namespace)

    @dlt.transformer(data_from=json_resource("unmapped"), columns=Graph)
    def unmapped_graph(resources):
        for resource in resources:
            yield build_graph(GenericNode, resource)

    @dlt.transformer(data_from=json_resource("nodes"), columns=Graph)
    def nodes_graph(nodes):
        for node in nodes:
            yield build_graph(NodeOutput, node)

    @dlt.transformer(data_from=json_resource("deployments"), columns=Graph)
    def deployments_graph(deployments):
        for deployment in deployments:
            yield build_graph(DeploymentNode, deployment)

    @dlt.transformer(data_from=json_resource("replicasets"), columns=Graph)
    def replicasets_graph(replicasets):
        for replicaset in replicasets:
            yield build_graph(ReplicaSetNode, replicaset)

    @dlt.transformer(data_from=json_resource("service_accounts"), columns=Graph)
    def service_accounts_graph(service_accounts):
        for service_account in service_accounts:
            yield build_graph(ServiceAccountNode, service_account)

    @dlt.transformer(data_from=json_resource("roles"), columns=Graph)
    def roles_graph(roles):
        for role in roles:
            yield build_graph(RoleNode, role)

    @dlt.transformer(data_from=json_resource("role_bindings"), columns=Graph)
    def role_bindings_graph(role_bindings):
        for role_binding in role_bindings:
            yield build_graph(RoleBindingNode, role_binding)

    @dlt.transformer(data_from=json_resource("cluster_roles"), columns=Graph)
    def cluster_roles_graph(roles):
        for role in roles:
            yield build_graph(ClusterRoleNode, role)

    @dlt.transformer(data_from=json_resource("cluster_role_bindings"), columns=Graph)
    def cluster_role_bindings_graph(cluster_role_bindings):
        for cluster_role_binding in cluster_role_bindings:
            yield build_graph(ClusterRoleBindingNode, cluster_role_binding)

    @dlt.transformer(data_from=json_resource("resource_definitions"), columns=Graph)
    def resource_definitions_graph(resource_definitions):
        for resource_definition in resource_definitions:
            yield build_graph(ResourceNode, resource_definition)

    @dlt.transformer(data_from=json_resource("cust_users"), columns=Graph)
    def users_graph(users):
        for user in users:
            yield build_graph(UserNode, user)

    @dlt.transformer(data_from=json_resource("cust_groups"), columns=Graph)
    def groups_graph(groups):
        for group in groups:
            yield build_graph(GroupNode, group)

    @dlt.transformer(data_from=json_resource("statefulsets"), columns=Graph)
    def statefulsets_graph(statefulsets):
        for statefulset in statefulsets:
            yield build_graph(StatefulSetNode, statefulset)

    @dlt.transformer(data_from=json_resource("daemonsets"), columns=Graph)
    def daemonsets_graph(daemonsets):
        for daemonset in daemonsets:
            yield build_graph(DaemonSetNode, daemonset)

    return (
        pods_graph,
        namespaces_graph,
        nodes_graph,
        service_accounts_graph,
        deployments_graph,
        replicasets_graph,
        statefulsets_graph,
        daemonsets_graph,
        roles_graph,
        role_bindings_graph,
        cluster_roles_graph,
        cluster_role_bindings_graph,
        resource_definitions_graph,
        users_graph,
        groups_graph,
        unmapped_graph,
        volumes_graph,
    )


@dlt.source(name="kubernetes_opengraph_eks")
def kubernetes_eks_opengraph(
    *,
    cluster: str,
    lookup: LookupManager,
):

    def build_graph(model_cls: Type[T], resource: dict) -> Graph:
        node = model_cls.from_input(**resource)
        node._cluster = cluster
        node._lookup = lookup

        entries = GraphEntries(
            nodes=[node],
            edges=[edge for edge in node.edges if edge],
        )
        return Graph(graph=entries)

    @dlt.resource(name="eks_virtual_cluster_roles", columns=Graph)
    def eks_cluster_roles():

        virtual_admin = EKSVirtualClusterAdminRole()
        print(virtual_admin.model_dump())

        yield build_graph(ClusterRoleNode, virtual_admin.model_dump())

    return eks_cluster_roles

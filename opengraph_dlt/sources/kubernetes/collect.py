from kubernetes import client, config
from kubernetes.dynamic import DynamicClient
from opengraph_dlt.sources.kubernetes.lookup import KubernetesLookup
from .models.pod import Pod, Volume as PodVolume
from .models.volume import Volume
from .models.namespace import Namespace
from .models.daemonset import DaemonSet
from .models.replicaset import ReplicaSet
from .models.statefulset import StatefulSet
from .models.deployment import Deployment
from .models.resource_group import ResourceGroup
from .models.generic import Generic
from .models.node import Node as KubeNode
from .models.role import Role
from .models.role_binding import RoleBinding
from .models.cluster_role import ClusterRole
from .models.cluster_role_binding import ClusterRoleBinding
from .models.service_account import ServiceAccount
from .models.resource import Resource
from .models.graph import Node as GraphNode, Graph, GraphEntries
from .models.identities import User, Group
from .models.cluster import Cluster
from .models.eks.eks_cluster_role import EKSVirtualClusterAdminRole
from urllib3.util.retry import Retry
import dlt
from typing import TypeVar


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
def kubernetes_resources(kube_config: None | str = None, cluster: str | None = None):

    config.load_kube_config(kube_config)

    configuration = client.Configuration.get_default_copy()
    configuration.retries = Retry(
        total=10,
        backoff_factor=2,
        respect_retry_after_header=True,
        status_forcelist=[429],
    )
    api_client = client.ApiClient(configuration=configuration)
    dyn_client = DynamicClient(api_client)

    @dlt.resource(
        columns=Cluster,
        table_name="clusters",
    )
    def clusters():
        yield {"name": cluster}

    @dlt.resource(columns=KubeNode, table_name="nodes", parallelized=True)
    def nodes():
        v1 = client.CoreV1Api(api_client)
        nodes = v1.list_node()
        for node in nodes.items:
            yield node.to_dict()

    @dlt.resource(columns=Namespace, table_name="namespaces", parallelized=True)
    def namespaces():
        v1 = client.CoreV1Api(api_client)
        namespaces = v1.list_namespace()
        for ns in namespaces.items:
            yield ns.to_dict()

    @dlt.resource(columns=DaemonSet, table_name="daemonsets", parallelized=True)
    def daemonsets():
        v1 = client.AppsV1Api(api_client)
        daemonsets = v1.list_daemon_set_for_all_namespaces()
        for daemonset in daemonsets.items:
            yield daemonset.to_dict()

    @dlt.resource(columns=StatefulSet, table_name="statefulsets", parallelized=True)
    def statefulsets():
        v1 = client.AppsV1Api(api_client)
        statefulsets = v1.list_stateful_set_for_all_namespaces()
        for replica in statefulsets.items:
            yield replica.to_dict()

    @dlt.resource(columns=ReplicaSet, table_name="replicasets", parallelized=True)
    def replicasets():
        v1 = client.AppsV1Api(api_client)
        replicasets = v1.list_replica_set_for_all_namespaces()
        for replica in replicasets.items:
            yield replica.to_dict()

    @dlt.resource(columns=Deployment, table_name="deployments", parallelized=True)
    def deployments():
        v1 = client.AppsV1Api(api_client)
        deployments = v1.list_deployment_for_all_namespaces()
        for deployment in deployments.items:
            yield deployment.to_dict()

    @dlt.resource(columns=Pod, table_name="pods", parallelized=True)
    def pods():
        v1 = client.CoreV1Api(api_client)
        pods = v1.list_pod_for_all_namespaces()
        for pod in pods.items:
            yield pod.to_dict()

    @dlt.transformer(data_from=pods, columns=Volume, table_name="cust_volumes")
    def volumes(pod: dict):
        volumes = pod["spec"]["volumes"]
        if volumes:
            node_name = pod["spec"].get("node_name")
            if not node_name:
                return
            for volume in volumes:
                host_path = volume.get("host_path")
                if not host_path:
                    continue
                path = host_path.get("path")
                yield {"node_name": node_name, "path": path}

    @dlt.resource(columns=Role, table_name="roles", parallelized=True)
    def roles():
        v1 = client.RbacAuthorizationV1Api(api_client)
        roles = v1.list_role_for_all_namespaces()
        for role in roles.items:
            yield role.to_dict()

    @dlt.resource(columns=RoleBinding, table_name="role_bindings", parallelized=True)
    def role_bindings():
        v1 = client.RbacAuthorizationV1Api(api_client)
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
        v1 = client.RbacAuthorizationV1Api(api_client)
        roles = v1.list_cluster_role()
        for role in roles.items:
            yield role.to_dict()

    @dlt.resource(
        columns=ClusterRoleBinding,
        table_name="cluster_role_bindings",
        parallelized=True,
    )
    def cluster_role_bindings():
        v1 = client.RbacAuthorizationV1Api(api_client)
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
        clusters,
    )


@dlt.source(name="kubernetes_opengraph_eks")
def kubernetes_eks_opengraph(
    *,
    cluster: str,
    lookup: KubernetesLookup,
):

    def build_graph(model_cls, resource: dict) -> Graph:
        resource_model = model_cls(**resource)
        resource_model._cluster = cluster
        resource_model._lookup = lookup
        node = resource_model.as_node

        entries = GraphEntries(
            nodes=[node],
            edges=[edge for edge in node.edges if edge],
        )
        return Graph(graph=entries)

    @dlt.resource(name="eks_virtual_cluster_roles", columns=Graph)
    def eks_cluster_roles():

        virtual_admin = EKSVirtualClusterAdminRole()
        print(virtual_admin.model_dump())

        yield build_graph(ClusterRole, virtual_admin.model_dump())

    return eks_cluster_roles

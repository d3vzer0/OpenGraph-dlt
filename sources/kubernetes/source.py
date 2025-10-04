from typing_extensions import Annotated
from kubernetes import client, config
from pathlib import Path
from enum import Enum
from sources.kubernetes.utils.lookup import LookupManager

from .models.k8s.pod import Pod, PodNode
from .models.k8s.namespace import Namespace, NamespaceNode
from .models.k8s.daemonset import DaemonSet, DaemonSetNode
from .models.k8s.replicaset import ReplicaSet, ReplicaSetNode
from .models.k8s.statefulset import StatefulSet, StatefulSetNode
from .models.k8s.deployment import Deployment, DeploymentNode

from .models.k8s.node import Node as KubeNode, NodeOutput
from .models.k8s.role import Role, RoleNode
from .models.k8s.role_binding import RoleBinding, RoleBindingNode
from .models.k8s.cluster_role import ClusterRole, ClusterRoleNode
from .models.k8s.cluster_role_binding import ClusterRoleBinding, ClusterRoleBindingNode
from .models.k8s.service_account import ServiceAccount, ServiceAccountNode
from .models.k8s.resource import Resource, ResourceNode
from .models.graph import GraphEntries, Graph
from .models.entries import Node as GraphNode
import json

# from dataclasses import dataclass
# import duckdb
import dlt
from typing import Type, TypeVar

T = TypeVar("T", bound=GraphNode)
E = TypeVar("E", bound=GraphEntries)

#
lookup = LookupManager()
# lookup.con = duckdb.connect(database="k8s.duckdb", read_only=False)


class ResourceGraph:
    def __init__(
        self,
        model_class: Type[T],
        cluster: str,
        lookup: None | LookupManager = None,
    ):
        self.model_class = model_class
        self.cluster = cluster
        self.lookup = lookup if lookup else LookupManager()

    def to_graph(self, resource: dict) -> Graph:
        graph_entries = GraphEntries()
        node = self.model_class.from_input(**resource)
        node._lookup = self.lookup
        node._cluster = self.cluster
        graph_entries.nodes.append(node)
        for edge in node.edges:
            graph_entries.edges.append(edge)
        return Graph(graph=graph_entries)


@dlt.source
def kubernetes_resources(
    kube_config: None | str = None, cluster: str = dlt.config.value
):
    config.load_kube_config(kube_config)
    lookup = LookupManager()

    def to_graph(model_class, resource):
        graph_entries = GraphEntries()
        node = model_class.from_input(**resource)
        node._lookup = lookup
        node._cluster = cluster
        graph_entries.nodes.append(node)
        for edge in node.edges:
            graph_entries.edges.append(edge)
        return Graph(graph=graph_entries)

    @dlt.resource(columns=KubeNode)
    def nodes():
        v1 = client.CoreV1Api()
        nodes = v1.list_node()
        for node in nodes.items:
            yield node.to_dict()

    @dlt.resource(columns=Namespace)
    def namespaces():
        v1 = client.CoreV1Api()
        namespaces = v1.list_namespace()
        for ns in namespaces.items:
            yield ns.to_dict()

    @dlt.resource(columns=DaemonSet)
    def daemonsets():
        v1 = client.AppsV1Api()
        daemonsets = v1.list_daemon_set_for_all_namespaces()
        for daemonset in daemonsets.items:
            yield daemonset.to_dict()

    @dlt.resource(columns=ReplicaSet)
    def statefulsets():
        v1 = client.AppsV1Api()
        statefulsets = v1.list_stateful_set_for_all_namespaces()
        for replica in statefulsets.items:
            yield replica.to_dict()

    @dlt.resource()
    def replicasets():
        v1 = client.AppsV1Api()
        replicasets = v1.list_replica_set_for_all_namespaces()
        for replica in replicasets.items:
            yield replica.to_dict()

    @dlt.resource()
    def deployments():
        v1 = client.AppsV1Api()
        deployments = v1.list_deployment_for_all_namespaces()
        for deployment in deployments.items:
            yield deployment.to_dict()

    @dlt.resource(columns=Pod)
    def pods():
        v1 = client.CoreV1Api()
        pods = v1.list_pod_for_all_namespaces()
        for pod in pods.items:
            yield pod.to_dict()

    @dlt.resource(columns=Role)
    def roles():
        v1 = client.RbacAuthorizationV1Api()
        roles = v1.list_role_for_all_namespaces()
        for role in roles.items:
            yield role.to_dict()

    @dlt.resource(columns=RoleBinding)
    def role_bindings():
        v1 = client.RbacAuthorizationV1Api()
        rolebs = v1.list_role_binding_for_all_namespaces()
        for roleb in rolebs.items:
            yield roleb.to_dict()

    @dlt.resource(columns=ClusterRole)
    def cluster_roles():
        v1 = client.RbacAuthorizationV1Api()
        roles = v1.list_cluster_role()
        for role in roles.items:
            yield role.to_dict()

    @dlt.resource(columns=ClusterRoleBinding)
    def cluster_role_bindings():
        v1 = client.RbacAuthorizationV1Api()
        rolebs = v1.list_cluster_role_binding()
        for roleb in rolebs.items:
            yield roleb.to_dict()

    @dlt.resource(columns=ServiceAccount)
    def service_accounts():
        v1 = client.CoreV1Api()
        service_accounts = v1.list_service_account_for_all_namespaces()
        for service_account in service_accounts.items:
            yield service_account.to_dict()

    @dlt.resource(columns=Resource)
    def resource_definitions():
        v1 = client.CoreV1Api()
        core_resources = v1.get_api_resources()
        for core_resource in core_resources.resources:
            yield core_resource.to_dict()

    @dlt.transformer(data_from=nodes, columns=Graph)
    def kube_node_graph(node: dict):
        yield to_graph(NodeOutput, node)

    @dlt.transformer(data_from=pods, columns=Graph)
    def pod_graph(pod: dict):
        yield to_graph(PodNode, pod)

    @dlt.transformer(data_from=deployments, columns=Graph)
    def deployment_graph(deployment: dict):
        yield to_graph(DeploymentNode, deployment)

    @dlt.transformer(data_from=replicasets, columns=Graph)
    def replicaset_graph(replicaset: dict):
        yield to_graph(ReplicaSetNode, replicaset)

    @dlt.transformer(data_from=replicasets, columns=Graph)
    def statefulset_graph(statefulset: dict):
        yield to_graph(StatefulSetNode, statefulset)

    @dlt.transformer(data_from=replicasets, columns=Graph)
    def daemonset_graph(daemonset: dict):
        yield to_graph(DaemonSetNode, daemonset)

    @dlt.transformer(data_from=namespaces, columns=Graph)
    def namespace_graph(namespace: dict):
        yield to_graph(NamespaceNode, namespace)

    @dlt.transformer(data_from=service_accounts, columns=Graph)
    def service_account_graph(service_account: dict):
        yield to_graph(ServiceAccountNode, service_account)

    @dlt.transformer(data_from=roles, columns=Graph)
    def role_graph(role: dict):
        yield to_graph(RoleNode, role)

    @dlt.transformer(data_from=role_bindings, columns=Graph)
    def role_binding_graph(role_binding: dict):
        yield to_graph(RoleBindingNode, role_binding)

    @dlt.transformer(data_from=cluster_roles, columns=Graph)
    def cluster_role_graph(role_binding: dict):
        yield to_graph(ClusterRoleNode, role_binding)

    @dlt.transformer(data_from=cluster_role_bindings, columns=Graph)
    def cluster_role_binding_graph(cluster_role_binding: dict):
        yield to_graph(ClusterRoleNode, cluster_role_binding)

    @dlt.transformer(data_from=resource_definitions, columns=Graph)
    def resource_definition_graph(resource_definition: dict):
        yield to_graph(ResourceGraph, resource_definition)

    return (
        pod_graph,
        namespace_graph,
        service_account_graph,
        deployment_graph,
        daemonset_graph,
        replicaset_graph,
        statefulset_graph,
        kube_node_graph,
        role_binding_graph,
        # role_graph,
        cluster_role_binding_graph,
        # cluster_role_graph,
    )

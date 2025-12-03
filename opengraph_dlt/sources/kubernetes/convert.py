from opengraph_dlt.sources.kubernetes.lookup import KubernetesLookup
from .models.pod import Pod
from .models.volume import Volume
from .models.namespace import Namespace
from .models.daemonset import DaemonSet
from .models.replicaset import ReplicaSet
from .models.statefulset import StatefulSet
from .models.deployment import Deployment
from .models.generic import Generic
from .models.node import KubeNode
from .models.role import Role
from .models.role_binding import RoleBinding
from .models.cluster_role import ClusterRole
from .models.cluster_role_binding import ClusterRoleBinding
from .models.service_account import ServiceAccount
from .models.resource import Resource
from .models.graph import Graph, GraphEntries
from .models.identities import User, Group
from .models.cluster import Cluster
from dlt.sources.filesystem import (
    filesystem as filesystemsource,
    read_jsonl,
)

import dlt


KUBERNETES_NODES = {
    "nodes": KubeNode,
    "pods": Pod,
    "cust_volumes": Volume,
    "namespaces": Namespace,
    "unmapped": Generic,
    "deployments": Deployment,
    "replicasets": ReplicaSet,
    "service_accounts": ServiceAccount,
    "roles": Role,
    "role_bindings": RoleBinding,
    "cluster_roles": ClusterRole,
    "cluster_role_bindings": ClusterRoleBinding,
    "resource_definitions": Resource,
    "cust_users": User,
    "cust_groups": Group,
    "statefulsets": StatefulSet,
    "daemonsets": DaemonSet,
    "clusters": Cluster,
}


@dlt.source(name="kubernetes_opengraph")
def kubernetes_opengraph(
    *,
    cluster: str,
    lookup: KubernetesLookup,
    bucket_url: str = dlt.config.value,
):

    def json_resource(subdir: str):
        files = filesystemsource(
            bucket_url=bucket_url,
            file_glob=f"{subdir}/**/*.jsonl.gz",
        )
        reader = (files | read_jsonl()).with_name(f"{subdir}_fs")
        return reader

    def build_graph(nodes, model):
        for node in nodes:
            resource = model(**node)
            resource._cluster = cluster
            resource._lookup = lookup
            graph_node = resource.as_node
            entries = GraphEntries(
                nodes=[graph_node],
                edges=[edge for edge in resource.edges if edge],
            )
            yield Graph(graph=entries)

    for table, model in KUBERNETES_NODES.items():
        reader = json_resource(table)
        yield dlt.resource(
            build_graph(reader, model),
            name=f"{table}_fs",
            columns=Graph,
            parallelized=False,
        )

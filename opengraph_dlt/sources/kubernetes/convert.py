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


# @dlt.source(name="kubernetes_opengraph")
# def kubernetes_opengraph(
#     *,
#     cluster: str,
#     lookup: KubernetesLookup,
#     bucket_url: str = dlt.config.value,
# ):

#     def json_resource(subdir: str):
#         files = filesystemsource(
#             bucket_url=bucket_url,
#             file_glob=f"{subdir}/**/*.jsonl.gz",
#         )
#         reader = (files | read_jsonl()).with_name(f"{subdir}_fs")
#         return reader

#     def build_graph(nodes, model):
#         for node in nodes:
#             resource = model(**node)
#             resource._cluster = cluster
#             resource._lookup = lookup
#             graph_node = resource.as_node
#             entries = GraphEntries(
#                 nodes=[graph_node],
#                 edges=[edge for edge in resource.edges if edge],
#             )
#             yield Graph(graph=entries)

#     for table, model in KUBERNETES_NODES.items():
#         reader = json_resource(table)
#         yield dlt.resource(
#             build_graph(reader, model),
#             name=f"{table}_fs",
#             columns=Graph,
#             parallelized=False,
#         )


@dlt.source(name="kubernetes_opengraph")
def kubernetes_opengraph(
    *,
    cluster: str,
    lookup: KubernetesLookup,
    bucket_url: str = dlt.config.value,
    chunk_size: int = dlt.config.value,
):

    @dlt.transformer(columns=Graph, max_table_nesting=0)
    def bundle_graph(resources, model):
        graph_entries = GraphEntries(nodes=[], edges=[])
        for resource in resources:
            resource_object = model(**resource)
            resource_object._cluster = cluster
            resource_object._lookup = lookup
            if hasattr(resource_object, "as_node"):
                graph_entries.nodes.append(resource_object.as_node)

            graph_entries.edges.extend(resource_object.edges)

            if len(graph_entries.nodes) + len(graph_entries.edges) >= chunk_size:
                yield Graph(graph=graph_entries)
                graph_entries = GraphEntries(nodes=[], edges=[])

        if graph_entries.nodes or graph_entries.edges:
            yield Graph(graph=graph_entries)

    for table, model in KUBERNETES_NODES.items():
        reader = (
            filesystemsource(bucket_url=bucket_url, file_glob=f"{table}/**/*.jsonl.gz")
            | read_jsonl()
        ).with_name(f"{table}_fs")

        yield (reader | bundle_graph(model)).with_name(f"{table}_fs_graph")

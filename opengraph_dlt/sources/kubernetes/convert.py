from opengraph_dlt.sources.kubernetes.lookup import KubernetesLookup
from .models.pod import PodNode
from .models.volume import VolumeNode
from .models.namespace import NamespaceNode
from .models.daemonset import DaemonSetNode
from .models.replicaset import ReplicaSetNode
from .models.statefulset import StatefulSetNode
from .models.deployment import DeploymentNode
from .models.generic import GenericNode
from .models.node import NodeOutput
from .models.role import RoleNode
from .models.role_binding import RoleBindingNode
from .models.cluster_role import ClusterRoleNode
from .models.cluster_role_binding import ClusterRoleBindingNode
from .models.service_account import ServiceAccountNode
from .models.resource import ResourceNode
from .models.graph import Graph, GraphEntries
from .models.identities import UserNode, GroupNode
from .models.cluster import ClusterNode
from dlt.sources.filesystem import (
    filesystem as filesystemsource,
    read_jsonl,
)

import dlt


KUBERNETES_NODES = {
    "nodes": NodeOutput,
    "pods": PodNode,
    "cust_volumes": VolumeNode,
    "namespaces": NamespaceNode,
    "unmapped": GenericNode,
    "deployments": DeploymentNode,
    "replicasets": ReplicaSetNode,
    "service_accounts": ServiceAccountNode,
    "roles": RoleNode,
    "role_bindings": RoleBindingNode,
    "cluster_roles": ClusterRoleNode,
    "cluster_role_bindings": ClusterRoleBindingNode,
    "resource_definitions": ResourceNode,
    "cust_users": UserNode,
    "cust_groups": GroupNode,
    "statefulsets": StatefulSetNode,
    "daemonsets": DaemonSetNode,
    "clusters": ClusterNode,
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
            node = model.from_input(**node)
            node._cluster = cluster
            node._lookup = lookup

            entries = GraphEntries(
                nodes=[node],
                edges=[edge for edge in node.edges if edge],
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

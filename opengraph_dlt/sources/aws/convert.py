from dlt.sources.filesystem import filesystem as filesystemsource, read_jsonl
from opengraph_dlt.sources.aws.models.group import Group
from opengraph_dlt.sources.aws.models.membership import UserGroupMembership
from opengraph_dlt.sources.aws.lookup import AWSLookup
from opengraph_dlt.sources.aws.models.role import Role

# from .models.eks import (
#     EKSClusterNode,
#     EKSAccessEntryEdges,
# )
from opengraph_dlt.sources.aws.models.pod_identity import EKSPodIdentity
from opengraph_dlt.sources.aws.models.user import User
from opengraph_dlt.sources.aws.models.policy import Policy
from opengraph_dlt.sources.aws.models.inline_policy import InlinePolicy
from opengraph_dlt.sources.aws.models.policy_attachments import PolicyAttachment
from opengraph_dlt.sources.aws.models.resource import Resource
from opengraph_dlt.sources.aws.models.graph import GraphEntries, Graph, Node, Edge

import dlt

AWS_NODES = {
    "policies": Policy,
    "groups": Group,
    "user_group_memberships": UserGroupMembership,
    "users": User,
    "roles": Role,
    "policy_attachments": PolicyAttachment,
    "inline_policies": InlinePolicy,
    # "eks": EKSClusterNode,
    # "eks_cluster_access_entries": EKSAccessEntryEdges,
    # "eks_pod_identity_associations": EKSPodIdentityEdges,
    "resources": Resource,
}


@dlt.source(name="aws_opengraph")
def aws_opengraph(
    *,
    lookup: AWSLookup,
    bucket_url: str = dlt.config.value,
    chunk_size: int = dlt.config.value,
):

    @dlt.transformer(columns=Graph, max_table_nesting=0)
    def bundle_graph(resources, model):
        graph_entries = GraphEntries(nodes=[], edges=[])
        for resource in resources:
            resource_object = model(**resource)
            resource_object._lookup = lookup
            if hasattr(resource_object, "as_node"):
                graph_entries.nodes.append(resource_object.as_node)

            graph_entries.edges.extend(resource_object.edges)

            if len(graph_entries.nodes) + len(graph_entries.edges) >= chunk_size:
                yield Graph(graph=graph_entries)
                graph_entries = GraphEntries(nodes=[], edges=[])

        yield Graph(graph=graph_entries)

    for table, model in AWS_NODES.items():
        reader = (
            filesystemsource(bucket_url=bucket_url, file_glob=f"{table}/**/*.jsonl.gz")
            | read_jsonl()
        ).with_name(f"{table}_fs")

        yield (reader | bundle_graph(model)).with_name(f"{table}_fs_graph")

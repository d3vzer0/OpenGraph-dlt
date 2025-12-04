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

# from opengraph_dlt.sources.aws.models.graph import GraphEntries, Graph, Node, Edge
from opengraph_dlt.sources.shared.convert import generate_graph

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
    def aws_context(obj):
        obj._lookup = lookup

    for table, model in AWS_NODES.items():
        reader = (
            filesystemsource(bucket_url=bucket_url, file_glob=f"{table}/**/*.jsonl.gz")
            | read_jsonl()
        ).with_name(f"{table}_fs")

        yield (
            reader
            | generate_graph(model, apply_context=aws_context, chunk_size=chunk_size)
        ).with_name(f"{table}_fs_graph")

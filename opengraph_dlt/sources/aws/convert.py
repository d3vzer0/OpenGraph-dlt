from dlt.sources.filesystem import filesystem as filesystemsource, read_jsonl
from .models.group import Group
from .models.membership import UserGroupMembership
from opengraph_dlt.sources.aws.lookup import AWSLookup
from .models.graph import Node
from .models.role import Role

# from .models.eks import (
#     EKSClusterNode,
#     EKSAccessEntryEdges,
# )
from .models.pod_identity import EKSPodIdentity
from .models.user import User
from .models.policy import Policy
from .models.inline_policy import InlinePolicy
from .models.policy_attachments import PolicyAttachment
from .models.resource import Resource
from .models.graph import (
    GraphEntries,
    Graph,
)
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
):

    def json_resource(subdir: str):
        files = filesystemsource(
            bucket_url=bucket_url,
            file_glob=f"{subdir}/**/*.jsonl.gz",
        )
        return (files | read_jsonl()).with_name(f"{subdir}_fs")

    def parse_nodes(resources: list, model):
        for resource in resources:
            resource_object = model(**resource)
            resource_object._lookup = lookup
            entries = GraphEntries(
                nodes=(
                    [resource_object.as_node]
                    if hasattr(resource_object, "as_node")
                    else []
                ),
                edges=[edge for edge in resource_object.edges if edge],
            )

            yield Graph(graph=entries)

    for table, model in AWS_NODES.items():
        reader = json_resource(table)
        yield dlt.resource(
            parse_nodes(reader, model),
            name=f"{table}_fs",
            columns=Graph,
            parallelized=False,
        )

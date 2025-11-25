from dlt.sources.filesystem import filesystem as filesystemsource, read_jsonl
from .models.group import GroupNode
from .models.membership import MembershipEdges
from opengraph_dlt.sources.aws.lookup import AWSLookup
from .models.graph import Node
from .models.role import RoleNode
from .models.eks import (
    EKSClusterNode,
    EKSAccessEntryEdges,
)
from .models.pod_identity import EKSPodIdentityEdges
from .models.user import UserNode
from .models.policy import (
    PolicyNode,
    InlinePolicyNode,
    PolicyAttachmentEdges,
)
from .models.resource import ResourceNode
from .models.graph import (
    GraphEntries,
    Graph,
)
import dlt

AWS_NODES = {
    "policies": PolicyNode,
    "groups": GroupNode,
    "user_group_memberships": MembershipEdges,
    "users": UserNode,
    "roles": RoleNode,
    "policy_attachments": PolicyAttachmentEdges,
    "inline_policies": InlinePolicyNode,
    "eks": EKSClusterNode,
    "eks_cluster_access_entries": EKSAccessEntryEdges,
    "eks_pod_identity_associations": EKSPodIdentityEdges,
    "resources": ResourceNode,
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

    def parse_nodes(nodes, model):
        for node in nodes:
            node = model.from_input(**node)
            node._lookup = lookup
            entries = GraphEntries(
                nodes=[node] if isinstance(node, Node) else [],
                edges=[edge for edge in node.edges if edge],
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

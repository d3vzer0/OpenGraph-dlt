from typing import List, Literal
from sources.kubernetes.models.cluster_role import (
    ClusterRole,
    Verbs,
    Metadata,
    Rule,
)


class VirtMetadata(Metadata):
    uid: str = "eks-virtual-admin"


class EKSVirtualClusterAdminRole(ClusterRole):
    kind: Literal["ClusterRole"] = "ClusterRole"
    metadata: Metadata = VirtMetadata(name="eks-virtual-cluster-admin")
    rules: List[Rule] = [
        Rule(api_groups=["*"], resources=["*"], verbs=[Verbs.wildcard]),
        Rule(api_groups=[], resources=[], verbs=[Verbs.wildcard]),
    ]


class VirtViewMetadata(Metadata):
    uid: str = "eks-virtual-admin-view"


class EKSVirtualAdminViewRole(ClusterRole):
    kind: Literal["ClusterRole"] = "ClusterRole"
    metadata: Metadata = VirtViewMetadata(name="eks-virtual-admin-view")
    rules: List[Rule] = [
        Rule(
            api_groups=["*"],
            resources=["*"],
            verbs=[Verbs.get, Verbs.list, Verbs.watch],
        )
    ]

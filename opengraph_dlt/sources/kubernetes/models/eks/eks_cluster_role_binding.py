from typing import List, Literal, Optional
from pydantic import BaseModel, Field
from opengraph_dlt.sources.kubernetes.models.cluster_role_binding import (
    ClusterRoleBinding,
    Metadata,
    Subject,
)


class EKSVirtualClusterAdminRoleBinding(ClusterRoleBinding):
    kind: Literal["ClusterRoleBinding"] = "ClusterRoleBinding"
    metadata: Metadata = Metadata(name="eks-virtual-cluster-admin-binding")
    roleRef: dict = {
        "apiGroup": "rbac.authorization.k8s.io",
        "kind": "ClusterRole",
        "name": "eks-virtual-cluster-admin",
    }
    subjects: List[Subject] = []


class EKSVirtualAdminViewRoleBinding(ClusterRoleBinding):
    kind: Literal["ClusterRoleBinding"] = "ClusterRoleBinding"
    metadata: Metadata = Metadata(name="eks-virtual-admin-view-binding")
    roleRef: dict = {
        "apiGroup": "rbac.authorization.k8s.io",
        "kind": "ClusterRole",
        "name": "eks-virtual-admin-view",
    }
    subjects: List[Subject] = []

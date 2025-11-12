from typing import List, Literal
from opengraph_dlt.sources.kubernetes.models.role_binding import RoleBinding, Metadata, Subject


class EKSVirtualAdminRoleBinding(RoleBinding):
    kind: Literal["RoleBinding"] = "RoleBinding"
    metadata: Metadata = Metadata(name="eks-virtual-admin-binding")
    roleRef: dict = {
        "apiGroup": "rbac.authorization.k8s.io",
        "kind": "Role",
        "name": "eks-virtual-admin",
    }
    subjects: List[Subject] = []


class EKSVirtualEditRoleBinding(RoleBinding):
    kind: Literal["RoleBinding"] = "RoleBinding"
    metadata: Metadata = Metadata(name="eks-virtual-edit-binding")
    roleRef: dict = {
        "apiGroup": "rbac.authorization.k8s.io",
        "kind": "Role",
        "name": "eks-virtual-edit",
    }
    subjects: List[Subject] = []


class EKSVirtualViewRoleBinding(RoleBinding):
    kind: Literal["RoleBinding"] = "RoleBinding"
    metadata: Metadata = Metadata(name="eks-virtual-view-binding")
    roleRef: dict = {
        "apiGroup": "rbac.authorization.k8s.io",
        "kind": "Role",
        "name": "eks-virtual-view",
    }
    subjects: List[Subject] = []

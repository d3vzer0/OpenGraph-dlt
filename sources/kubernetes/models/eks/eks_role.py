from typing import List, Literal, Optional
from pydantic import BaseModel, Field

from sources.kubernetes.models.role import Role, Metadata, Rule, Verbs


class EKSVirtualAdminRole(Role):
    kind: Literal["Role"] = "Role"
    metadata: Metadata = Metadata(name="eks-virtual-admin")
    rules: List[Rule] = [
        Rule(
            api_groups=["apps"],
            resources=[
                "daemonsets",
                "deployments",
                "deployments/rollback",
                "deployments/scale",
                "replicasets",
                "replicasets/scale",
                "statefulsets",
                "statefulsets/scale",
            ],
            verbs=[
                Verbs.create,
                Verbs.delete,
                Verbs.deletecollection,
                Verbs.patch,
                Verbs.update,
            ],
        ),
        Rule(
            api_groups=["apps"],
            resources=[
                "controllerrevisions",
                "daemonsets",
                "daemonsets/status",
                "deployments",
                "deployments/scale",
                "deployments/status",
                "replicasets",
                "replicasets/scale",
                "replicasets/status",
                "statefulsets",
                "statefulsets/scale",
                "statefulsets/status",
            ],
            verbs=[Verbs.get, Verbs.list, Verbs.watch],
        ),
        Rule(
            api_groups=["authorization.k8s.io"],
            resources=["localsubjectaccessreviews"],
            verbs=[Verbs.create],
        ),
        Rule(
            api_groups=["autoscaling"],
            resources=["horizontalpodautoscalers"],
            verbs=[
                Verbs.create,
                Verbs.delete,
                Verbs.deletecollection,
                Verbs.patch,
                Verbs.update,
            ],
        ),
        Rule(
            api_groups=["autoscaling"],
            resources=["horizontalpodautoscalers", "horizontalpodautoscalers/status"],
            verbs=[Verbs.get, Verbs.list, Verbs.watch],
        ),
        Rule(
            api_groups=["batch"],
            resources=["cronjobs", "jobs"],
            verbs=[
                Verbs.create,
                Verbs.delete,
                Verbs.deletecollection,
                Verbs.patch,
                Verbs.update,
            ],
        ),
        Rule(
            api_groups=["batch"],
            resources=["cronjobs", "cronjobs/status", "jobs", "jobs/status"],
            verbs=[Verbs.get, Verbs.list, Verbs.watch],
        ),
        Rule(
            api_groups=["discovery.k8s.io"],
            resources=["endpointslices"],
            verbs=[Verbs.get, Verbs.list, Verbs.watch],
        ),
        Rule(
            api_groups=["extensions"],
            resources=[
                "daemonsets",
                "deployments",
                "deployments/rollback",
                "deployments/scale",
                "ingresses",
                "networkpolicies",
                "replicasets",
                "replicasets/scale",
                "replicationcontrollers/scale",
            ],
            verbs=[
                Verbs.create,
                Verbs.delete,
                Verbs.deletecollection,
                Verbs.patch,
                Verbs.update,
            ],
        ),
        Rule(
            api_groups=["extensions"],
            resources=[
                "daemonsets",
                "daemonsets/status",
                "deployments",
                "deployments/scale",
                "deployments/status",
                "ingresses",
                "ingresses/status",
                "networkpolicies",
                "replicasets",
                "replicasets/scale",
                "replicasets/status",
                "replicationcontrollers/scale",
            ],
            verbs=[Verbs.get, Verbs.list, Verbs.watch],
        ),
        Rule(
            api_groups=["networking.k8s.io"],
            resources=["ingresses", "networkpolicies"],
            verbs=[
                Verbs.create,
                Verbs.delete,
                Verbs.deletecollection,
                Verbs.patch,
                Verbs.update,
            ],
        ),
        Rule(
            api_groups=["networking.k8s.io"],
            resources=["ingresses", "ingresses/status", "networkpolicies"],
            verbs=[Verbs.get, Verbs.list, Verbs.watch],
        ),
        # policy
        Rule(
            api_groups=["policy"],
            resources=["poddisruptionbudgets"],
            verbs=[
                Verbs.create,
                Verbs.delete,
                Verbs.deletecollection,
                Verbs.patch,
                Verbs.update,
            ],
        ),
        Rule(
            api_groups=["policy"],
            resources=["poddisruptionbudgets", "poddisruptionbudgets/status"],
            verbs=[Verbs.get, Verbs.list, Verbs.watch],
        ),
        Rule(
            api_groups=["rbac.authorization.k8s.io"],
            resources=["roles", "rolebindings"],
            verbs=[
                Verbs.create,
                Verbs.delete,
                Verbs.deletecollection,
                Verbs.get,
                Verbs.list,
                Verbs.patch,
                Verbs.update,
                Verbs.watch,
            ],
        ),
        Rule(
            api_groups=[""],
            resources=[
                "configmaps",
                "endpoints",
                "persistentvolumeclaims",
                "persistentvolumeclaims/status",
                "pods",
                "replicationcontrollers",
                "replicationcontrollers/scale",
                "serviceaccounts",
                "services",
                "services/status",
            ],
            verbs=[Verbs.get, Verbs.list, Verbs.watch],
        ),
        Rule(
            api_groups=[""],
            resources=[
                "pods/attach",
                "pods/exec",
                "pods/portforward",
                "pods/proxy",
                "secrets",
                "services/proxy",
            ],
            verbs=[Verbs.get, Verbs.list, Verbs.watch],
        ),
        Rule(
            api_groups=[""],
            resources=[
                "configmaps",
                "events",
                "persistentvolumeclaims",
                "replicationcontrollers",
                "replicationcontrollers/scale",
                "secrets",
                "serviceaccounts",
                "services",
                "services/proxy",
            ],
            verbs=[
                Verbs.create,
                Verbs.delete,
                Verbs.deletecollection,
                Verbs.patch,
                Verbs.update,
            ],
        ),
        Rule(
            api_groups=[""],
            resources=[
                "pods",
                "pods/attach",
                "pods/exec",
                "pods/portforward",
                "pods/proxy",
            ],
            verbs=[
                Verbs.create,
                Verbs.delete,
                Verbs.deletecollection,
                Verbs.patch,
                Verbs.update,
            ],
        ),
        Rule(api_groups=[""], resources=["serviceaccounts"], verbs=[Verbs.impersonate]),
        Rule(
            api_groups=[""],
            resources=[
                "bindings",
                "events",
                "limitranges",
                "namespaces/status",
                "pods/log",
                "pods/status",
                "replicationcontrollers/status",
                "resourcequotas",
                "resourcequotas/status",
            ],
            verbs=[Verbs.get, Verbs.list, Verbs.watch],
        ),
        Rule(
            api_groups=[""],
            resources=["namespaces"],
            verbs=[Verbs.get, Verbs.list, Verbs.watch],
        ),
    ]


class EKSVirtualEditRole(Role):
    kind: Literal["Role"] = "Role"
    metadata: Metadata = Metadata(name="eks-virtual-edit")
    rules: List[Rule] = [
        Rule(
            api_groups=["apps"],
            resources=[
                "daemonsets",
                "deployments",
                "deployments/rollback",
                "deployments/scale",
                "replicasets",
                "replicasets/scale",
                "statefulsets",
                "statefulsets/scale",
            ],
            verbs=[
                Verbs.create,
                Verbs.delete,
                Verbs.deletecollection,
                Verbs.patch,
                Verbs.update,
            ],
        ),
        Rule(
            api_groups=["apps"],
            resources=[
                "controllerrevisions",
                "daemonsets",
                "daemonsets/status",
                "deployments",
                "deployments/scale",
                "deployments/status",
                "replicasets",
                "replicasets/scale",
                "replicasets/status",
                "statefulsets",
                "statefulsets/scale",
                "statefulsets/status",
            ],
            verbs=[Verbs.get, Verbs.list, Verbs.watch],
        ),
        # autoscaling
        Rule(
            api_groups=["autoscaling"],
            resources=["horizontalpodautoscalers", "horizontalpodautoscalers/status"],
            verbs=[Verbs.get, Verbs.list, Verbs.watch],
        ),
        Rule(
            api_groups=["autoscaling"],
            resources=["horizontalpodautoscalers"],
            verbs=[
                Verbs.create,
                Verbs.delete,
                Verbs.deletecollection,
                Verbs.patch,
                Verbs.update,
            ],
        ),
        # batch
        Rule(
            api_groups=["batch"],
            resources=["cronjobs", "jobs"],
            verbs=[
                Verbs.create,
                Verbs.delete,
                Verbs.deletecollection,
                Verbs.patch,
                Verbs.update,
            ],
        ),
        Rule(
            api_groups=["batch"],
            resources=["cronjobs", "cronjobs/status", "jobs", "jobs/status"],
            verbs=[Verbs.get, Verbs.list, Verbs.watch],
        ),
        Rule(
            api_groups=["discovery.k8s.io"],
            resources=["endpointslices"],
            verbs=[Verbs.get, Verbs.list, Verbs.watch],
        ),
        Rule(
            api_groups=["extensions"],
            resources=[
                "daemonsets",
                "deployments",
                "deployments/rollback",
                "deployments/scale",
                "ingresses",
                "networkpolicies",
                "replicasets",
                "replicasets/scale",
                "replicationcontrollers/scale",
            ],
            verbs=[
                Verbs.create,
                Verbs.delete,
                Verbs.deletecollection,
                Verbs.patch,
                Verbs.update,
            ],
        ),
        Rule(
            api_groups=["extensions"],
            resources=[
                "daemonsets",
                "daemonsets/status",
                "deployments",
                "deployments/scale",
                "deployments/status",
                "ingresses",
                "ingresses/status",
                "networkpolicies",
                "replicasets",
                "replicasets/scale",
                "replicasets/status",
                "replicationcontrollers/scale",
            ],
            verbs=[Verbs.get, Verbs.list, Verbs.watch],
        ),
        # networking.k8s.io
        Rule(
            api_groups=["networking.k8s.io"],
            resources=["ingresses", "networkpolicies"],
            verbs=[
                Verbs.create,
                Verbs.delete,
                Verbs.deletecollection,
                Verbs.patch,
                Verbs.update,
            ],
        ),
        Rule(
            api_groups=["networking.k8s.io"],
            resources=["ingresses", "ingresses/status", "networkpolicies"],
            verbs=[Verbs.get, Verbs.list, Verbs.watch],
        ),
        # policy
        Rule(
            api_groups=["policy"],
            resources=["poddisruptionbudgets"],
            verbs=[
                Verbs.create,
                Verbs.delete,
                Verbs.deletecollection,
                Verbs.patch,
                Verbs.update,
            ],
        ),
        Rule(
            api_groups=["policy"],
            resources=["poddisruptionbudgets", "poddisruptionbudgets/status"],
            verbs=[Verbs.get, Verbs.list, Verbs.watch],
        ),
        Rule(
            api_groups=[""],
            resources=[
                "pods",
                "pods/attach",
                "pods/exec",
                "pods/portforward",
                "pods/proxy",
            ],
            verbs=[
                Verbs.create,
                Verbs.delete,
                Verbs.deletecollection,
                Verbs.patch,
                Verbs.update,
            ],
        ),
        Rule(
            api_groups=[""],
            resources=[
                "configmaps",
                "events",
                "persistentvolumeclaims",
                "replicationcontrollers",
                "replicationcontrollers/scale",
                "secrets",
                "serviceaccounts",
                "services",
                "services/proxy",
            ],
            verbs=[
                Verbs.create,
                Verbs.delete,
                Verbs.deletecollection,
                Verbs.patch,
                Verbs.update,
            ],
        ),
        Rule(
            api_groups=[""],
            resources=[
                "configmaps",
                "endpoints",
                "persistentvolumeclaims",
                "persistentvolumeclaims/status",
                "pods",
                "replicationcontrollers",
                "replicationcontrollers/scale",
                "serviceaccounts",
                "services",
                "services/status",
            ],
            verbs=[Verbs.get, Verbs.list, Verbs.watch],
        ),
        Rule(
            api_groups=[""],
            resources=[
                "pods/attach",
                "pods/exec",
                "pods/portforward",
                "pods/proxy",
                "secrets",
                "services/proxy",
            ],
            verbs=[Verbs.get, Verbs.list, Verbs.watch],
        ),
        Rule(
            api_groups=[""],
            resources=[
                "bindings",
                "events",
                "limitranges",
                "namespaces/status",
                "pods/log",
                "pods/status",
                "replicationcontrollers/status",
                "resourcequotas",
                "resourcequotas/status",
            ],
            verbs=[Verbs.get, Verbs.list, Verbs.watch],
        ),
        Rule(
            api_groups=[""],
            resources=["namespaces"],
            verbs=[Verbs.get, Verbs.list, Verbs.watch],
        ),
        Rule(api_groups=[""], resources=["serviceaccounts"], verbs=[Verbs.impersonate]),
    ]


class EKSVirtualViewRole(Role):
    kind: Literal["Role"] = "Role"
    metadata: Metadata = Metadata(name="eks-virtual-view")
    rules: List[Rule] = [
        Rule(
            api_groups=["apps"],
            resources=[
                "controllerrevisions",
                "daemonsets",
                "daemonsets/status",
                "deployments",
                "deployments/scale",
                "deployments/status",
                "replicasets",
                "replicasets/scale",
                "replicasets/status",
                "statefulsets",
                "statefulsets/scale",
                "statefulsets/status",
            ],
            verbs=[Verbs.get, Verbs.list, Verbs.watch],
        ),
        # autoscaling
        Rule(
            api_groups=["autoscaling"],
            resources=["horizontalpodautoscalers", "horizontalpodautoscalers/status"],
            verbs=[Verbs.get, Verbs.list, Verbs.watch],
        ),
        # batch
        Rule(
            api_groups=["batch"],
            resources=["cronjobs", "cronjobs/status", "jobs", "jobs/status"],
            verbs=[Verbs.get, Verbs.list, Verbs.watch],
        ),
        # discovery.k8s.io
        Rule(
            api_groups=["discovery.k8s.io"],
            resources=["endpointslices"],
            verbs=[Verbs.get, Verbs.list, Verbs.watch],
        ),
        # extensions (compat)
        Rule(
            api_groups=["extensions"],
            resources=[
                "daemonsets",
                "daemonsets/status",
                "deployments",
                "deployments/scale",
                "deployments/status",
                "ingresses",
                "ingresses/status",
                "networkpolicies",
                "replicasets",
                "replicasets/scale",
                "replicasets/status",
                "replicationcontrollers/scale",
            ],
            verbs=[Verbs.get, Verbs.list, Verbs.watch],
        ),
        # networking.k8s.io
        Rule(
            api_groups=["networking.k8s.io"],
            resources=["ingresses", "ingresses/status", "networkpolicies"],
            verbs=[Verbs.get, Verbs.list, Verbs.watch],
        ),
        # policy
        Rule(
            api_groups=["policy"],
            resources=["poddisruptionbudgets", "poddisruptionbudgets/status"],
            verbs=[Verbs.get, Verbs.list, Verbs.watch],
        ),
        # core API (no secrets)
        Rule(
            api_groups=[""],
            resources=[
                "configmaps",
                "endpoints",
                "persistentvolumeclaims",
                "persistentvolumeclaims/status",
                "pods",
                "replicationcontrollers",
                "replicationcontrollers/scale",
                "serviceaccounts",
                "services",
                "services/status",
            ],
            verbs=[Verbs.get, Verbs.list, Verbs.watch],
        ),
        Rule(
            api_groups=[""],
            resources=[
                "bindings",
                "events",
                "limitranges",
                "namespaces/status",
                "pods/log",
                "pods/status",
                "replicationcontrollers/status",
                "resourcequotas",
                "resourcequotas/status",
            ],
            verbs=[Verbs.get, Verbs.list, Verbs.watch],
        ),
        Rule(
            api_groups=[""],
            resources=["namespaces"],
            verbs=[Verbs.get, Verbs.list, Verbs.watch],
        ),
    ]

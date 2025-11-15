from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr
from opengraph_dlt.sources.aws.models.graph import Node, Edge, AWSCollector, NodeTypes
from opengraph_dlt.sources.kubernetes.models.cluster import Cluster
from opengraph_dlt.sources.kubernetes.models.identities import GroupNode
from opengraph_dlt.sources.shared.models.entries import EdgePath, NodeProperties


AWS_EKS_ACCESS_POLICY_GROUPS = {
    "AmazonEKSClusterAdminPolicy": ["system:masters", "system:authenticated"],
    "AmazonEKSServicePolicy": ["eks:service-operations", "system:authenticated"],
    "AmazonEKSPrometheusPolicy": ["system:monitoring", "system:authenticated"],
    "AmazonEKSClusterInsightsPolicy": ["system:monitoring"],
    "AmazonEKSAdminPolicy": ["system:authenticated"],
    "AmazonEKSAdminViewPolicy": ["system:authenticated"],
    "AmazonEKSEditPolicy": ["system:authenticated"],
    "AmazonEKSViewPolicy": ["system:authenticated"],
}


class EKSCluster(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    name: str = Field(alias="name")
    arn: str = Field(alias="arn")
    status: Optional[str] = Field(alias="status", default=None)
    version: Optional[str] = Field(alias="version", default=None)
    created_at: Optional[datetime] = Field(alias="createdAt", default=None)
    endpoint: Optional[str] = Field(alias="endpoint", default=None)
    role_arn: Optional[str] = Field(alias="roleArn", default=None)
    account_id: Optional[str] = Field(alias="accountId", default=None)
    region: Optional[str] = Field(alias="region", default=None)


class EKSClusterNode(Node):
    properties: NodeProperties

    @property
    def _managed_by(self):
        k8s_cluster = Cluster(name=self.properties.name)
        start = EdgePath(value=k8s_cluster.uid, match_by="id")
        end = EdgePath(value=self.id, match_by="id")
        return [Edge(start=start, end=end, kind="K8sManagedBy")]

    @property
    def edges(self) -> list[Edge]:
        return [*self._managed_by]

    @classmethod
    def from_input(cls, **kwargs) -> "EKSClusterNode":
        model = EKSCluster(**kwargs)
        extra_properties = {
            "aws_account_id": model.account_id,
            "arn": model.arn,
            "version": model.version,
            "status": model.status,
            "endpoint": model.endpoint,
            "role_arn": model.role_arn,
            "aws_region": model.region,
            "created_at": model.created_at,
        }
        props = NodeProperties(
            name=model.name, displayname=model.name, **extra_properties
        )
        node = cls(kinds=[NodeTypes.AWSEKSCluster.value], properties=props)
        node.attach_context(model.account_id, scope=model.region)
        return node


class AccessScope(BaseModel):
    type: str
    namespaces: list[str]


class AccessPolicy(BaseModel):
    policy_arn: str = Field(alias="policyArn")
    access_scope: AccessScope = Field(alias="accessScope")


class EKSAccesssEntry(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    cluster_name: str = Field(alias="clusterName")
    principal_arn: str = Field(alias="principalArn")
    access_entry_arn: str = Field(alias="accessEntryArn")
    kubernetes_groups: list[str] = Field(alias="kubernetesGroups")
    account_id: str = Field(alias="accountId")
    policies: list[AccessPolicy]
    region: str
    username: str


class EKSAccessEntryEdges(BaseModel):
    _access_entry: EKSAccesssEntry = PrivateAttr()

    _ENTITY_NODE_TYPES = {
        "user": "AWSUser",
        "role": "AWSRole",
        "group": "AWSGroup",
    }

    @property
    def entity_type(self):
        parts = self._access_entry.principal_arn.split(":", 5)
        resource = parts[5]
        prefix = resource.split("/", 1)[0]
        return prefix

    @property
    def principal_guid(self) -> str:
        node_type = self._ENTITY_NODE_TYPES[self.entity_type]
        return AWSCollector.guid(
            name=self._access_entry.principal_arn,
            node_type=node_type,
            account_id=self._access_entry.account_id,
        )

    @property
    def access_policies(self):
        all_policy_edges = []
        for policy in self._access_entry.policies:
            eks_groups = AWS_EKS_ACCESS_POLICY_GROUPS.get(
                policy.policy_arn.split("/")[-1], ["system:authenticated"]
            )
            start = EdgePath(value=self.principal_guid, match_by="id")
            for group_name in eks_groups:
                group = GroupNode.from_input(name=group_name, api_group="")
                group._cluster = self._access_entry.cluster_name
                end = EdgePath(value=group.id, match_by="id")
                all_policy_edges.append(Edge(start=start, end=end, kind="K8sMemberOf"))

        return all_policy_edges

    @property
    def edges(self) -> list[Edge]:
        return [*self.access_policies]

    @classmethod
    def from_input(cls, **kwargs) -> "EKSAccessEntryEdges":
        model = EKSAccesssEntry(**kwargs)
        edges = cls()
        edges._access_entry = model
        return edges

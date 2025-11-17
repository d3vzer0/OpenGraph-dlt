from pydantic import BaseModel, ConfigDict, Field, PrivateAttr
from opengraph_dlt.sources.aws.models.graph import Node, Edge, NodeTypes
from opengraph_dlt.sources.aws.models.graph import AWSCollector
from opengraph_dlt.sources.kubernetes.models.graph import (
    KubernetesCollector,
    NodeTypes as KubeNodeTypes,
)
from opengraph_dlt.sources.shared.models.entries import EdgePath


class EKSPodIdentity(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    cluster_name: str = Field(alias="clusterName")
    association_arn: str = Field(alias="associationArn")
    owner_arn: str | None = Field(alias="ownerArn", default=None)
    role_arn: str = Field(alias="roleArn")
    service_account: str = Field(alias="serviceAccount")
    association_id: str = Field(alias="associationId")
    namespace: str


class EKSPodIdentityEdges(BaseModel):
    _access_entry: EKSPodIdentity = PrivateAttr()

    @property
    def _aws_to_kube(self):
        start_account_id = self._access_entry.role_arn.split(":")[4]
        start_guid = AWSCollector.guid(
            self._access_entry.role_arn, NodeTypes.AWSRole, start_account_id
        )
        start_path = EdgePath(value=start_guid, match_by="id")

        end_id = KubernetesCollector.guid(
            self._access_entry.service_account,
            KubeNodeTypes.KubeServiceAccount,
            self._access_entry.cluster_name,
            self._access_entry.namespace,
        )
        end_path = EdgePath(value=end_id, match_by="id")
        return Edge(kind="KubeRunsAs", start=start_path, end=end_path)

    @property
    def _kube_to_aws(self):
        start_id = KubernetesCollector.guid(
            self._access_entry.service_account,
            KubeNodeTypes.KubeServiceAccount,
            self._access_entry.cluster_name,
            self._access_entry.namespace,
        )
        start_path = EdgePath(value=start_id, match_by="id")

        end_account_id = self._access_entry.role_arn.split(":")[4]
        end_guid = AWSCollector.guid(
            self._access_entry.role_arn, NodeTypes.AWSRole, end_account_id
        )
        end_path = EdgePath(value=end_guid, match_by="id")

        return Edge(kind="AWSAllowsAssume", start=start_path, end=end_path)

    @property
    def edges(self) -> list[Edge]:
        return [self._aws_to_kube, self._kube_to_aws]

    @classmethod
    def from_input(cls, **kwargs) -> "EKSPodIdentityEdges":
        model = EKSPodIdentity(**kwargs)
        edges = cls()
        edges._access_entry = model
        return edges

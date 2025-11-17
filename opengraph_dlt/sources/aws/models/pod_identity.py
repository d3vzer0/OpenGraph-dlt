from pydantic import BaseModel, ConfigDict, Field, PrivateAttr
from opengraph_dlt.sources.aws.models.graph import Node, Edge


class EKSPodIdentity(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    cluster_name: str = Field(alias="clusterName")
    association_arn: str = Field(alias="associationArn")
    owner_arn: str | None = Field(alias="ownerArn", default=None)
    service_account: str = Field(alias="serviceAccount")
    namespace: str


class EKSPodIdentityEdge(BaseModel):
    _access_entry: EKSPodIdentity = PrivateAttr()

    @property
    def edges(self) -> list[Edge]:
        return []

    @classmethod
    def from_input(cls, **kwargs) -> "EKSPodIdentityEdge":
        model = EKSPodIdentity(**kwargs)
        edges = cls()
        edges._access_entry = model
        return edges

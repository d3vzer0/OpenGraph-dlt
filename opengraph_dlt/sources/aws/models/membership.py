from pydantic import BaseModel, ConfigDict, Field
from opengraph_dlt.sources.shared.models.entries import EdgePath, Edge
from opengraph_dlt.sources.aws.models.graph import NodeTypes, AWSCollector
from opengraph_dlt.sources.shared.models.docs import graph_resource, EdgeDef


@graph_resource(
    edges=[
        EdgeDef(
            start=NodeTypes.AWSUser.value,
            end=NodeTypes.AWSGroup.value,
            kind="AWSMemberOf",
            description="User to Group membership",
        )
    ]
)
class UserGroupMembership(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    user_name: str = Field(alias="UserName")
    user_arn: str = Field(alias="UserArn")
    group_name: str = Field(alias="GroupName")
    group_id: str = Field(alias="GroupId")
    group_arn: str = Field(alias="GroupArn")
    account_id: str = Field(alias="AccountId")

    @property
    def _user_id(self) -> str:
        return AWSCollector.guid(
            name=self.user_arn,
            node_type=NodeTypes.AWSUser,
            account_id=self.account_id,
        )

    @property
    def _group_id(self) -> str:
        return AWSCollector.guid(
            name=self.group_arn,
            node_type=NodeTypes.AWSGroup,
            account_id=self.account_id,
        )

    @property
    def edges(self) -> list[Edge]:
        start = EdgePath(value=self._user_id, match_by="id")
        end = EdgePath(value=self._group_id, match_by="id")
        return [Edge(kind="AWSMemberOf", start=start, end=end)]

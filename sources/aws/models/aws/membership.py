from pydantic import BaseModel, ConfigDict, Field, PrivateAttr
from sources.aws.utils.lookup import LookupManager
from sources.aws.utils.guid import gen_guid, NodeTypes
from sources.aws.models.entries import Edge, EdgePath, EdgeProperties


class UserGroupMembership(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    user_name: str = Field(alias="UserName")
    user_arn: str = Field(alias="UserArn")
    group_name: str = Field(alias="GroupName")
    group_id: str = Field(alias="GroupId")
    group_arn: str = Field(alias="GroupArn")
    account_id: str = Field(alias="AccountId")


class MembershipEdges(BaseModel):
    membership: UserGroupMembership
    _lookup: LookupManager = PrivateAttr()

    @property
    def _user_id(self) -> str:
        return gen_guid(
            name=self.membership.user_arn,
            node_type=NodeTypes.AWSUser.value,
            account_id=self.membership.account_id,
        )

    @property
    def _group_id(self) -> str:
        return gen_guid(
            name=self.membership.group_arn,
            node_type=NodeTypes.AWSGroup.value,
            account_id=self.membership.account_id,
        )

    @property
    def edges(self) -> list[Edge]:
        start = EdgePath(value=self._user_id, match_by="id")
        end = EdgePath(value=self._group_id, match_by="id")
        return [Edge(kind="AWSMemberOf", start=start, end=end)]

    @classmethod
    def from_input(cls, **kwargs) -> "MembershipEdges":
        model = UserGroupMembership(**kwargs)
        return cls(membership=model)

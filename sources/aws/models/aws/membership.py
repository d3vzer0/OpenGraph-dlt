from pydantic import BaseModel, ConfigDict


class UserGroupMembership(BaseModel):
    model_config = ConfigDict(extra="allow")

    UserName: str
    GroupName: str
    GroupId: str
    GroupArn: str
    AccountId: str

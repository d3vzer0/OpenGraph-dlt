from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Literal


class Policy(BaseModel):
    PolicyName: str
    PolicyId: str
    Arn: str
    Path: str
    DefaultVersionId: str
    AttachmentCount: int
    CreateDate: datetime
    UpdateDate: datetime | None
    AccountId: str | None
    IsAWSManaged: bool


class PolicyAttachment(BaseModel):
    model_config = ConfigDict(extra="allow")
    PolicyArn: str
    EntityType: Literal["User", "Group", "Role"]
    EntityName: str
    EntityId: str
    EntityArn: str | None = None
    AccountId: str | None = None

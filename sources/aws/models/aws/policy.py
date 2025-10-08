from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Literal


class InlinePolicy(BaseModel):
    EntityType: Literal["User", "Group", "Role"]
    EntityName: str
    EntityId: str
    PolicyName: str
    PolicyDocument: dict


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
    PolicyDocument: dict


class PolicyAttachment(BaseModel):
    model_config = ConfigDict(extra="allow")
    PolicyArn: str
    EntityType: Literal["User", "Group", "Role"]
    EntityName: str
    EntityId: str
    EntityArn: str | None = None
    AccountId: str | None = None

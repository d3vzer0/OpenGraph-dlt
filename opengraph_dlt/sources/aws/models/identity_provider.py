from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from opengraph_dlt.sources.aws.utils.guid import NodeTypes
from opengraph_dlt.sources.aws.models.graph import Node, NodeProperties


class IdentityProvider(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    provider_arn: str = Field(alias="ProviderArn")
    provider_type: str = Field(alias="ProviderType")
    create_date: datetime = Field(alias="CreateDate")
    account_id: Optional[str] = Field(alias="AccountId", default=None)
    url: Optional[str] = Field(alias="Url", default=None)


class IdentityProviderProperties(NodeProperties):
    model_config = ConfigDict(extra="allow")
    provider_type: str
    url: Optional[str] = None


class IdentityProviderNode(Node):
    properties: IdentityProviderProperties

    @property
    def edges(self):
        return []

    @classmethod
    def from_input(cls, **kwargs) -> "IdentityProviderNode":
        model = IdentityProvider(**kwargs)
        display_name = model.provider_arn.split("/")[-1]
        properties = IdentityProviderProperties(
            name=model.provider_arn,
            displayname=display_name,
            aws_account_id=model.account_id,
            provider_type=model.provider_type,
            arn=model.provider_arn,
            url=model.url,
            created_at=model.create_date,
        )
        node = cls(kinds=[NodeTypes.AWSIdentityProvider.value], properties=properties)
        node.attach_context(model.account_id)
        return node

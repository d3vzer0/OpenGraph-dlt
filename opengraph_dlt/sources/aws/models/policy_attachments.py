from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr
from opengraph_dlt.sources.aws.models.graph import (
    NodeProperties,
    Node,
    NodeTypes,
    AWSCollector,
    BaseResource,
)
from opengraph_dlt.sources.shared.models.entries import Edge, EdgePath, EdgeProperties
from opengraph_dlt.sources.aws.lookup import AWSLookup
from opengraph_dlt.sources.shared.docs import graph_resource, EdgeDef

ENTITY_NODE_TYPES = {
    "User": "AWSUser",
    "Group": "AWSGroup",
    "Role": "AWSRole",
}


class ExtendedAttachmentProperties(EdgeProperties):
    entity_type: str


class PolicyAttachmentEdges(BaseModel):
    properties: ExtendedAttachmentProperties


@graph_resource(
    edges=[
        EdgeDef(
            start="AWSUser",
            end="AWSPolicy",
            kind="AWSAttachesPolicy",
            description="User attaches policy",
        ),
        EdgeDef(
            start="AWSGroup",
            end="AWSPolicy",
            kind="AWSAttachesPolicy",
            description="Group attaches policy",
        ),
        EdgeDef(
            start="AWSRole",
            end="AWSPolicy",
            kind="AWSAttachesPolicy",
            description="Role attaches policy",
        ),
    ]
)
class PolicyAttachment(BaseResource):
    model_config = ConfigDict(extra="allow", populate_by_name=True)
    policy_arn: str = Field(alias="PolicyArn")
    entity_type: Literal["User", "Group", "Role"] = Field(alias="EntityType")
    entity_name: str = Field(alias="EntityName")
    entity_id: str = Field(alias="EntityId")
    entity_arn: str | None = Field(alias="EntityArn", default=None)
    account_id: str | None = Field(alias="AccountId", default=None)
    policy_document: dict = Field(alias="PolicyDocument")

    @property
    def _policy_guid(self) -> str:
        return AWSCollector.guid(
            name=self.policy_arn,
            node_type=NodeTypes.AWSPolicy,
            account_id=self.account_id,
        )

    @property
    def _principal_guid(self) -> str:
        lookup_arn = {
            "User": self._lookup.user,
            "Group": self._lookup.group,
            "Role": self._lookup.role,
        }
        node_type = ENTITY_NODE_TYPES[self.entity_type]
        source_key = lookup_arn[self.entity_type](self.entity_name)
        return AWSCollector.guid(
            name=source_key,
            node_type=node_type,
            account_id=self.account_id,
        )

    @property
    def edges(self) -> list[Edge]:
        start = EdgePath(value=self._principal_guid, match_by="id")
        end = EdgePath(value=self._policy_guid, match_by="id")
        properties = ExtendedAttachmentProperties(entity_type=self.entity_type)
        return [
            Edge(kind="AWSAttachesPolicy", start=start, end=end, properties=properties)
        ]

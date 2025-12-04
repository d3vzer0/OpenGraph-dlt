from collections.abc import Iterator
from datetime import datetime

from pydantic import ConfigDict, Field
from opengraph_dlt.sources.aws.models.graph import (
    NodeProperties,
    Node,
    NodeTypes,
    AWSCollector,
    BaseResource,
)
from opengraph_dlt.sources.shared.models.entries import Edge, EdgePath
from opengraph_dlt.sources.shared.docs import graph_resource, NodeDef


ENTITY_NODE_TYPES = {
    "User": "AWSUser",
    "Group": "AWSGroup",
    "Role": "AWSRole",
}


def flatten_principals(principal_obj: dict) -> list[str]:
    principals: list[str] = []
    for key, value in principal_obj.items():
        if isinstance(value, list):
            principals.extend(value)
        elif isinstance(value, str):
            principals.append(value)
        elif isinstance(value, dict):
            principals.extend(flatten_principals(value))
    return principals


class ExtendedPolicyProperties(NodeProperties):
    model_config = ConfigDict(extra="allow", populate_by_name=True)
    is_aws_managed: bool


class PolicyNode(Node):
    properties: ExtendedPolicyProperties


@graph_resource(node=NodeDef(kind="AWSPolicy", description="AWS IAM policy node"))
class Policy(BaseResource):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    policy_name: str = Field(alias="PolicyName")
    policy_id: str = Field(alias="PolicyId")
    arn: str = Field(alias="Arn")
    path: str = Field(alias="Path")
    default_version_id: str = Field(alias="DefaultVersionId")
    attachment_count: int = Field(alias="AttachmentCount")
    create_date: datetime = Field(alias="CreateDate")
    update_date: datetime | None = Field(alias="UpdateDate", default=None)
    account_id: str | None = Field(alias="AccountId", default=None)
    is_aws_managed: bool = Field(alias="IsAWSManaged")
    policy_document: dict = Field(alias="PolicyDocument")

    def _impacted_resources(self, resources: list[str]) -> list[dict]:
        all_resources = []
        for resource in resources:
            find_resources = self._lookup.allowed_resources(resource)
            for resource_arn, region, resource_type, account in find_resources:
                all_resources.append(
                    {
                        "arn": resource_arn,
                        "region": region,
                        "resource_type": resource_type,
                        "account": account,
                    }
                )
        return all_resources

    @property
    def _has_permissions(self) -> Iterator[Edge]:
        start_path = EdgePath(value=self.as_node.id, match_by="id")
        for statement in self.policy_document["Statement"]:
            resources = statement.get("Resource")
            resources = resources if isinstance(resources, list) else [resources]
            impacted_resources = self._impacted_resources(resources)
            for rec in impacted_resources:
                kind = AWSCollector.gen_node_type(rec["resource_type"])
                end_id = AWSCollector.guid(
                    rec["arn"], kind, rec["account"], rec["region"]
                )
                end_path = EdgePath(value=end_id, match_by="id")
                yield Edge(kind="AWSCanAction", start=start_path, end=end_path)

    @property
    def edges(self) -> Iterator[Edge]:
        yield from ()

    @property
    def as_node(self) -> "PolicyNode":
        properties = ExtendedPolicyProperties(
            name=self.policy_name,
            displayname=self.policy_name,
            aws_account_id=self.account_id,
            aws_region="global",
            arn=self.arn,
            created_at=self.create_date,
            is_aws_managed=self.is_aws_managed,
        )
        node = PolicyNode(kinds=[NodeTypes.AWSPolicy.value], properties=properties)
        node.attach_context(self.account_id)
        return node

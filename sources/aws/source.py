from dlt.sources.filesystem import filesystem as filesystemsource, read_jsonl
from .models.aws.group import Group, GroupNode
from .models.aws.membership import UserGroupMembership
from .models.aws.role import Role, RoleNode
from .models.aws.user import User, UserNode
from .models.aws.policy import Policy, PolicyAttachment
from .models.entries import Edge, EdgePath, EdgeProperties, Node as GraphNode
from .models.graph import GraphEntries, Graph
import boto3
import dlt
from typing import TypeVar

T = TypeVar("T", bound=GraphNode)


@dlt.source(name="aws_resources")
def aws_resources(
    *,
    profile_name: str | None = None,
    region_name: str | None = None,
    endpoint_url: str | None = None,
):
    session = boto3.session.Session(profile_name=profile_name, region_name=region_name)
    iam = session.client("iam", endpoint_url=endpoint_url)
    sts = session.client("sts", endpoint_url=endpoint_url)
    account_id = sts.get_caller_identity()["Account"]

    def _with_account(record: dict) -> dict:
        record["AccountId"] = account_id
        return record

    @dlt.resource(name="users", columns=User, primary_key="UserId", parallelized=True)
    def users():
        paginator = iam.get_paginator("list_users")
        for page in paginator.paginate():
            for user in page.get("Users", []):
                yield _with_account(user)

    @dlt.resource(
        name="groups", columns=Group, primary_key="GroupId", parallelized=True
    )
    def groups():
        paginator = iam.get_paginator("list_groups")
        for page in paginator.paginate():
            for group in page.get("Groups", []):
                yield _with_account(group)

    @dlt.resource(name="roles", columns=Role, primary_key="RoleId", parallelized=True)
    def roles():
        paginator = iam.get_paginator("list_roles")
        for page in paginator.paginate():
            for role in page.get("Roles", []):
                yield _with_account(role)

    @dlt.transformer(
        data_from=users,
        name="user_group_memberships",
        columns=UserGroupMembership,
        parallelized=True,
    )
    def user_group_memberships(user):
        username = user["UserName"]
        groups_response = iam.list_groups_for_user(UserName=username)
        for group in groups_response.get("Groups", []):
            yield {
                "UserName": username,
                "GroupName": group["GroupName"],
                "GroupId": group["GroupId"],
                "GroupArn": group["Arn"],
                "AccountId": account_id,
            }

    @dlt.resource(name="policies", columns=Policy, parallelized=True)
    def policies():
        paginator = iam.get_paginator("list_policies")
        for page in paginator.paginate(Scope="All", OnlyAttached=True):
            for policy in page.get("Policies", []):
                policy["AccountId"] = policy.get("Arn", "").split(":")[4] or account_id
                policy["IsAWSManaged"] = policy["Arn"].startswith(
                    "arn:aws:iam::aws:policy/"
                )
                yield policy

    @dlt.transformer(
        data_from=policies,
        name="policy_attachments",
        columns=PolicyAttachment,
        parallelized=True,
    )
    def policy_attachments(policy):
        arn = policy["Arn"]
        account = policy.get("AccountId") or account_id
        entities = iam.list_entities_for_policy(PolicyArn=arn)
        policy_attachments = {
            "PolicyUsers": {
                "EntityId": "UserId",
                "EntityType": "User",
                "EntityName": "UserName",
            },
            "PolicyGroups": {
                "EntityId": "GroupId",
                "EntityType": "Group",
                "EntityName": "GroupName",
            },
            "PolicyRoles": {
                "EntityId": "RoleId",
                "EntityType": "Role",
                "EntityName": "RoleName",
            },
        }

        for target, fields in policy_attachments.items():
            for entity in entities.get(target, []):
                yield {
                    "PolicyArn": arn,
                    "EntityType": fields["EntityType"],
                    "EntityName": entity.get(fields["EntityName"]),
                    "EntityId": entity.get(fields["EntityId"]),
                    "EntityArn": entity.get("Arn"),
                    "AccountId": account,
                }

    return (
        users,
        groups,
        roles,
        policies,
        user_group_memberships,
        policy_attachments,
    )


@dlt.source(name="aws_fs")
def aws_fs(bucket_url: str):
    def json_resource(subdir: str, resource_name: str):
        files = filesystemsource(
            bucket_url=bucket_url,
            file_glob=f"{subdir}/**/*.jsonl.gz",
        )
        return (files | read_jsonl()).with_name(resource_name)

    return (
        json_resource("users", "users"),
        # json_resource("groups", "groups"),
        # json_resource("roles", "roles"),
        # json_resource("user_group_memberships", "user_group_memberships"),
    )

from dlt.sources.filesystem import filesystem as filesystemsource, read_jsonl
from .models.aws.group import Group, GroupNode
from .models.aws.membership import UserGroupMembership, MembershipEdges
from sources.aws.utils.lookup import LookupManager
from .models.aws.role import Role, RoleNode
from .models.aws.user import User, UserNode
from .models.aws.policy import (
    Policy,
    PolicyNode,
    PolicyStatementOutput,
    PolicyAttachment,
    InlinePolicy,
    InlinePolicyNode,
    PolicyAttachmentEdges,
)
from .models.aws.ec2_instance import EC2Instance, EC2InstanceRole
from .models.aws.resource import Resource
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
    re = session.client("resource-explorer-2", region_name=region_name)
    ec2 = session.client("ec2", region_name=region_name)

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
        name="user_inline_policies",
        columns=InlinePolicy,
        data_from=users,
        table_name="inline_policies",
        parallelized=True,
    )
    def user_inline_policies(user: dict):
        paginator = iam.get_paginator("list_user_policies")
        user_name = user["UserName"]
        for page in paginator.paginate(UserName=user_name):
            for policy in page.get("PolicyNames", []):
                document = iam.get_user_policy(UserName=user_name, PolicyName=policy)
                yield {
                    "EntityType": "User",
                    "EntityName": user_name,
                    "EntityId": user["UserId"],
                    "EntityArn": user["Arn"],
                    "PolicyName": policy,
                    "PolicyDocument": document.get("PolicyDocument"),
                    "AccountId": account_id,
                }

    @dlt.transformer(
        name="group_inline_policies",
        columns=InlinePolicy,
        data_from=groups,
        table_name="inline_policies",
        parallelized=True,
    )
    def group_inline_policies(group: dict):
        paginator = iam.get_paginator("list_group_policies")
        group_name = group["GroupName"]
        for page in paginator.paginate(GroupName=group_name):
            for policy in page.get("PolicyNames", []):
                document = iam.get_group_policy(GroupName=group_name, PolicyName=policy)
                yield {
                    "EntityType": "Group",
                    "EntityName": group_name,
                    "EntityId": group["GroupId"],
                    "EntityArn": group["Arn"],
                    "PolicyName": policy,
                    "PolicyDocument": document.get("PolicyDocument"),
                    "AccountId": account_id,
                }

    @dlt.transformer(
        name="role_inline_policies",
        columns=InlinePolicy,
        data_from=roles,
        table_name="inline_policies",
        parallelized=True,
    )
    def role_inline_policies(role: dict):
        paginator = iam.get_paginator("list_role_policies")
        role_name = role["RoleName"]
        for page in paginator.paginate(RoleName=role_name):
            for policy in page.get("PolicyNames", []):
                document = iam.get_role_policy(RoleName=role_name, PolicyName=policy)
                yield {
                    "EntityType": "Role",
                    "EntityName": role_name,
                    "EntityId": role["RoleId"],
                    "EntityArn": role["Arn"],
                    "PolicyName": policy,
                    "PolicyDocument": document.get("PolicyDocument"),
                    "AccountId": account_id,
                }

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
                "UserArn": user["Arn"],
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
                version_id = policy["DefaultVersionId"]
                version = iam.get_policy_version(
                    PolicyArn=policy["Arn"],
                    VersionId=version_id,
                )
                policy["AccountId"] = policy.get("Arn", "").split(":")[4] or account_id
                policy["IsAWSManaged"] = policy["Arn"].startswith(
                    "arn:aws:iam::aws:policy/"
                )
                policy["PolicyDocument"] = version["PolicyVersion"]["Document"]
                yield policy

    @dlt.resource(name="resources", columns=Resource, parallelized=True)
    def resources():
        view_arn = re.list_views()["Views"][0]
        paginator = re.get_paginator("search")
        for page in paginator.paginate(
            ViewArn=view_arn, QueryString="arn", MaxResults=1000
        ):
            for resource in page.get("Resources", []):
                yield resource

    @dlt.transformer(
        name="ec2_instances",
        data_from=resources,
        columns=EC2Instance,
        parallelized=True,
    )
    def ec2_instances(resource):
        if resource["ResourceType"] == "ec2:instance":
            instance_id = resource["Arn"].split("/")[-1]
            instance_details = ec2.describe_instances(InstanceIds=[instance_id])
            for reservation in instance_details.get("Reservations", []):
                for instance in reservation.get("Instances", []):
                    yield instance

    @dlt.transformer(
        name="ec2_instance_roles",
        data_from=ec2_instances,
        columns=EC2InstanceRole,
        parallelized=True,
    )
    def ec2_instance_roles(instance):
        profile_info = instance["IamInstanceProfile"]
        if profile_info:
            profile_arn = profile_info["Arn"]
            profile_name = profile_arn.split("/")[-1]
            profile = iam.get_instance_profile(InstanceProfileName=profile_name)[
                "InstanceProfile"
            ]
            for role in profile.get("Roles", []):
                yield {
                    "InstanceId": instance["InstanceId"],
                    "InstanceArn": instance["Arn"],
                    "InstanceRegion": instance["Region"],
                    **role,
                }

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
                    "PolicyDocument": policy["PolicyDocument"],
                }

    return (
        users,
        groups,
        roles,
        policies,
        user_group_memberships,
        policy_attachments,
        resources,
        ec2_instances,
        ec2_instance_roles,
        user_inline_policies,
        group_inline_policies,
        role_inline_policies,
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
        json_resource("policy_attachments", "policy_attachments_fs"),
        json_resource("users", "users_fs"),
        json_resource("policies", "policies_fs"),
        json_resource("groups", "groups_fs"),
        json_resource("roles", "roles_fs"),
        json_resource("inline_policies", "inline_policies_fs"),
        json_resource("user_group_memberships", "user_group_memberships_fs"),
    )


@dlt.source(name="aws_opengraph")
def aws_opengraph(
    *,
    lookup: LookupManager,
    raw_source,
):

    def build_graph(model_cls, resource: dict) -> Graph:
        node = model_cls.from_input(**resource)
        node._lookup = lookup
        entries = GraphEntries(
            nodes=[node],
            edges=[edge for edge in node.edges if edge],
        )
        return Graph(graph=entries)

    def build_graph_edges(model_cls, resource: dict) -> Graph:
        node = model_cls.from_input(**resource)
        node._lookup = lookup
        entries = GraphEntries(
            nodes=[],
            edges=[edge for edge in node.edges],
        )
        return Graph(graph=entries)

    @dlt.transformer(data_from=raw_source.policies_fs, columns=Graph)
    def policies_graph(policies: list):
        for policy in policies:
            yield build_graph(PolicyNode, policy)

    @dlt.transformer(data_from=raw_source.groups_fs, columns=Graph)
    def groups_graph(groups: list):
        for group in groups:
            yield build_graph(GroupNode, group)

    @dlt.transformer(data_from=raw_source.user_group_memberships_fs, columns=Graph)
    def memberships_graph(memberships: list):
        for membership in memberships:
            yield build_graph_edges(MembershipEdges, membership)

    @dlt.transformer(data_from=raw_source.users_fs, columns=Graph)
    def users_graph(users: list):
        for user in users:
            yield build_graph(UserNode, user)

    @dlt.transformer(data_from=raw_source.roles_fs, columns=Graph)
    def roles_graph(roles: list):
        for role in roles:
            yield build_graph(RoleNode, role)

    @dlt.transformer(data_from=raw_source.policy_attachments_fs, columns=Graph)
    def policies_attachment_graph(policies: list):
        for policy in policies:
            yield build_graph_edges(PolicyAttachmentEdges, policy)

    @dlt.transformer(data_from=raw_source.inline_policies_fs, columns=Graph)
    def inline_policies_graph(policies: list):

        for policy in policies:
            yield build_graph(InlinePolicyNode, policy)

    return (
        users_graph,
        roles_graph,
        policies_attachment_graph,
        groups_graph,
        policies_graph,
        memberships_graph,
        inline_policies_graph,
    )

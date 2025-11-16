from dlt.sources.filesystem import filesystem as filesystemsource, read_jsonl
from .models.group import Group, GroupNode
from .models.membership import UserGroupMembership, MembershipEdges
from opengraph_dlt.sources.aws.lookup import AWSLookup
from .models.role import Role, RoleNode
from .models.eks import (
    EKSCluster,
    EKSAccesssEntry,
    EKSClusterNode,
    EKSAccessEntryEdges,
)
from .models.user import User, UserNode
from .models.policy import (
    Policy,
    PolicyNode,
    PolicyStatementOutput,
    PolicyAttachment,
    InlinePolicy,
    InlinePolicyNode,
    PolicyAttachmentEdges,
)
from .models.ec2_instance import EC2Instance, EC2InstanceRole
from .models.resource import Resource
from .models.graph import (
    Node as GraphNode,
    GraphEntries,
    Graph,
)
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
    eks_client = session.client("eks", region_name=region_name)

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

        @dlt.defer
        def _get_role_policy(user_name, policy):
            document = iam.get_user_policy(UserName=user_name, PolicyName=policy)
            return {
                "EntityType": "User",
                "EntityName": user_name,
                "EntityId": user["UserId"],
                "EntityArn": user["Arn"],
                "PolicyName": policy,
                "PolicyDocument": document.get("PolicyDocument"),
                "AccountId": account_id,
            }

        paginator = iam.get_paginator("list_user_policies")
        user_name = user["UserName"]
        for page in paginator.paginate(UserName=user_name):
            for policy in page.get("PolicyNames", []):
                yield _get_role_policy(user_name, policy)

    @dlt.transformer(
        name="group_inline_policies",
        columns=InlinePolicy,
        data_from=groups,
        table_name="inline_policies",
        parallelized=True,
    )
    def group_inline_policies(group: dict):

        @dlt.defer
        def _get_role_policy(group_name, policy):
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

        paginator = iam.get_paginator("list_group_policies")
        group_name = group["GroupName"]
        for page in paginator.paginate(GroupName=group_name):
            for policy in page.get("PolicyNames", []):
                yield _get_role_policy(group_name, policy)

    @dlt.transformer(
        name="role_inline_policies",
        columns=InlinePolicy,
        data_from=roles,
        table_name="inline_policies",
        parallelized=True,
    )
    def role_inline_policies(role: dict):

        @dlt.defer
        def _get_role_policy(role_name, policy):
            document = iam.get_role_policy(RoleName=role_name, PolicyName=policy)
            return {
                "EntityType": "Role",
                "EntityName": role_name,
                "EntityId": role["RoleId"],
                "EntityArn": role["Arn"],
                "PolicyName": policy,
                "PolicyDocument": document.get("PolicyDocument"),
                "AccountId": account_id,
            }

        paginator = iam.get_paginator("list_role_policies")
        role_name = role["RoleName"]
        for page in paginator.paginate(RoleName=role_name):
            for policy in page.get("PolicyNames", []):
                yield _get_role_policy(role_name, policy)

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

        @dlt.defer
        def _get_policy_version(policy):
            version = iam.get_policy_version(
                PolicyArn=policy["Arn"],
                VersionId=policy["DefaultVersionId"],
            )
            policy["AccountId"] = policy.get("Arn", "").split(":")[4] or account_id
            policy["IsAWSManaged"] = policy["Arn"].startswith(
                "arn:aws:iam::aws:policy/"
            )
            policy["PolicyDocument"] = version["PolicyVersion"]["Document"]
            return policy

        for page in paginator.paginate(
            Scope="All", OnlyAttached=True, PaginationConfig={"PageSize": 1000}
        ):
            for policy in page.get("Policies", []):
                yield _get_policy_version(policy)

    @dlt.resource(name="resources", columns=Resource, parallelized=True)
    def resources():
        view_arn = re.list_views()["Views"][0]
        paginator = re.get_paginator("search")
        for page in paginator.paginate(
            ViewArn=view_arn,
            QueryString="arn",
            PaginationConfig={
                "PageSize": 1000,
            },
        ):
            for resource in page.get("Resources", []):
                yield resource

    @dlt.resource(name="eks", columns=EKSCluster, parallelized=True)
    def eks():

        @dlt.defer
        def _get_cluster(cluster_name):
            cluster = eks_client.describe_cluster(name=cluster_name)["cluster"]
            cluster["accountId"] = cluster["arn"].split(":")[4]
            cluster["region"] = cluster["arn"].split(":")[3]
            return cluster

        paginator = eks_client.get_paginator("list_clusters")
        for page in paginator.paginate():
            for cluster_name in page.get("clusters", []):
                yield _get_cluster(cluster_name)

    @dlt.transformer(
        name="eks_cluster_access_entries",
        data_from=eks,
        columns=EKSAccesssEntry,
        parallelized=True,
    )
    def eks_cluster_access_entries(cluster: dict):
        region = cluster["arn"].split(":")[3]

        @dlt.defer
        def _describe_acces_entry(cluster, principal):

            detail = eks_client.describe_access_entry(
                clusterName=cluster["name"],
                principalArn=principal,
            )
            associated = eks_client.list_associated_access_policies(
                clusterName=cluster["name"],
                principalArn=principal,
            )
            return {
                **detail["accessEntry"],
                "accountId": cluster["accountId"],
                "region": cluster["region"],
                "policies": associated["associatedAccessPolicies"],
            }

        access_entries = eks_client.list_access_entries(clusterName=cluster["name"])
        for principal in access_entries["accessEntries"]:
            yield _describe_acces_entry(cluster, principal)

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

    # @dlt.transformer(
    #     name="ec2_instance_roles",
    #     data_from=ec2_instances,
    #     columns=EC2InstanceRole,
    #     parallelized=True,
    # )
    # def ec2_instance_roles(instance):
    #     profile_info = instance["IamInstanceProfile"]
    #     if profile_info:
    #         profile_arn = profile_info["Arn"]
    #         profile_name = profile_arn.split("/")[-1]
    #         profile = iam.get_instance_profile(InstanceProfileName=profile_name)[
    #             "InstanceProfile"
    #         ]
    #         for role in profile.get("Roles", []):
    #             yield {
    #                 "InstanceId": instance["InstanceId"],
    #                 "InstanceArn": instance["Arn"],
    #                 "InstanceRegion": instance["Region"],
    #                 **role,
    #             }

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

    yield (
        users,
        groups,
        roles,
        policies,
        user_group_memberships,
        policy_attachments,
        resources,
        ec2_instances,
        # ec2_instance_roles,
        user_inline_policies,
        group_inline_policies,
        role_inline_policies,
        eks,
        eks_cluster_access_entries,
    )


@dlt.source(name="aws_opengraph")
def aws_opengraph(
    *,
    lookup: AWSLookup,
    bucket_url: str = dlt.config.value,
):

    def json_resource(subdir: str):
        files = filesystemsource(
            bucket_url=bucket_url,
            file_glob=f"{subdir}/**/*.jsonl.gz",
        )
        return (files | read_jsonl()).with_name(f"{subdir}_fs")

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

    @dlt.transformer(data_from=json_resource("policies"), columns=Graph)
    def policies_graph(policies: list):
        for policy in policies:
            yield build_graph(PolicyNode, policy)

    @dlt.transformer(data_from=json_resource("groups"), columns=Graph)
    def groups_graph(groups: list):
        for group in groups:
            yield build_graph(GroupNode, group)

    @dlt.transformer(
        data_from=json_resource("user_group_memberships"),
        columns=Graph,
    )
    def memberships_graph(memberships: list):
        for membership in memberships:
            yield build_graph_edges(MembershipEdges, membership)

    @dlt.transformer(data_from=json_resource("users"), columns=Graph)
    def users_graph(users: list):
        for user in users:
            yield build_graph(UserNode, user)

    @dlt.transformer(data_from=json_resource("roles"), columns=Graph)
    def roles_graph(roles: list):
        for role in roles:
            yield build_graph(RoleNode, role)

    @dlt.transformer(
        data_from=json_resource("policy_attachments"),
        columns=Graph,
    )
    def policies_attachment_graph(policies: list):
        for policy in policies:
            yield build_graph_edges(PolicyAttachmentEdges, policy)

    @dlt.transformer(
        data_from=json_resource("inline_policies"),
        columns=Graph,
    )
    def inline_policies_graph(policies: list):
        for policy in policies:
            yield build_graph(InlinePolicyNode, policy)

    @dlt.transformer(data_from=json_resource("eks"), columns=Graph)
    def eks_graph(eks_clusters: list):
        for eks_cluster in eks_clusters:
            yield build_graph(EKSClusterNode, eks_cluster)

    @dlt.transformer(
        data_from=json_resource("eks_cluster_access_entries"),
        columns=Graph,
    )
    def eks_cluster_access_entries_graph(entries: list):
        for entry in entries:
            yield build_graph_edges(EKSAccessEntryEdges, entry)

    return (
        users_graph,
        roles_graph,
        policies_attachment_graph,
        groups_graph,
        policies_graph,
        memberships_graph,
        inline_policies_graph,
        eks_graph,
        eks_cluster_access_entries_graph,
    )

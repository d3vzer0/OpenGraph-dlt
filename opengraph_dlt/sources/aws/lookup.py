from duckdb import DuckDBPyConnection
from opengraph_dlt.sources.shared.lookup import LookupManager
from functools import lru_cache


class AWSLookup(LookupManager):

    def __init__(self, client: DuckDBPyConnection, schema: str = "aws"):
        super().__init__(client, schema)
        self.schema = schema
        self.client = client

    @lru_cache
    def group(self, group_name: str) -> str | None:
        return self._find_single_object(
            f"""SELECT
                arn
            FROM {self.schema}.groups
            WHERE group_name = ?;
            """,
            [group_name],
        )

    @lru_cache
    def user(self, user_name: str) -> str | None:
        return self._find_single_object(
            f"""SELECT
                arn
            FROM {self.schema}.users
            WHERE user_name = ?;
            """,
            [user_name],
        )

    @lru_cache
    def role(self, role_name: str) -> str | None:
        return self._find_single_object(
            f"""SELECT
                arn
            FROM {self.schema}.roles
            WHERE role_name = ?;
            """,
            [role_name],
        )

    @lru_cache
    def role_trusts(self, role_arn: str) -> list:
        return self._find_all_objects(
            f"""SELECT
            arn,
            role_name,
            condition,
            principal
            FROM {self.schema}.role_trust_statements
            WHERE arn = ? and effect = 'Allow' and action = 'sts:AssumeRole'
            """,
            [role_arn],
        )

    @lru_cache
    def used_policy(self, policy_arn: str) -> str | None:
        return self._find_single_object(
            f"""SELECT
            policy_arn
            FROM {self.schema}.used_policies
            WHERE policy_arn = ?
            """,
            [policy_arn],
        )

    @lru_cache
    def allowed_resources(self, target: str) -> list[tuple]:
        return self._find_all_objects(
            f"""SELECT
                arn,
                region,
                resource_type,
                owning_account_id
            FROM {self.schema}.resources_with_identities
            WHERE arn GLOB ?;""",
            [target],
        )

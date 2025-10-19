from duckdb import DuckDBPyConnection
from functools import lru_cache


class LookupManager:

    def __init__(self, client: DuckDBPyConnection, directory: str = "./output"):
        self.directory = directory
        self.schema = "aws_lookup.aws"
        self.staging_schema = "aws_lookup.aws_staging"
        self.client = client

    def _find_arn(self, *args) -> str:
        self.client.execute(*args)
        result = self.client.fetchone()
        return str(result[0]) if result else ""

    def _find_resources(self, *args) -> list:
        self.client.execute(*args)
        results = self.client.fetchall()
        return results

    @lru_cache
    def group(self, group_name: str) -> str:
        return self._find_arn(
            f"""SELECT
                arn
            FROM {self.schema}.groups
            WHERE group_name = ?;
            """,
            [group_name],
        )

    @lru_cache
    def user(self, user_name: str) -> str:
        return self._find_arn(
            f"""SELECT
                arn
            FROM {self.schema}.users
            WHERE user_name = ?;
            """,
            [user_name],
        )

    @lru_cache
    def role(self, role_name: str) -> str:
        return self._find_arn(
            f"""SELECT
                arn
            FROM {self.schema}.roles
            WHERE role_name = ?;
            """,
            [role_name],
        )

    @lru_cache
    def role_trusts(self, role_arn: str) -> list:
        return self._find_resources(
            f"""SELECT
            arn,
            role_name,
            condition,
            principal
            FROM {self.staging_schema}.role_trust_statements
            WHERE arn = ? and effect = 'Allow' and action = 'sts:AssumeRole'
            """,
            [role_arn],
        )

    @lru_cache
    def allowed_resources(self, target: str) -> list[tuple]:
        return self._find_resources(
            f"""SELECT 
                arn,
                region,
                resource_type
            FROM {self.schema}.resources
            WHERE arn GLOB ?;""",
            [target],
        )

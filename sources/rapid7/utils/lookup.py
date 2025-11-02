from duckdb import DuckDBPyConnection
from functools import lru_cache


class LookupManager:

    def __init__(
        self, client: DuckDBPyConnection, schema: str = "bloodhound_lookup.main"
    ):
        self.schema = schema
        self.client = client

    def _find_object_id(self, *args) -> str | None:
        self.client.execute(*args)
        result = self.client.fetchone()
        return str(result[0]) if result else None

    @lru_cache
    def find_asset(self, hostname: str) -> str | None:
        return self._find_object_id(
            f"""SELECT
                object_id
            FROM {self.schema}.nodes_api
            WHERE properties.name = ?;""",
            [hostname],
        )

from duckdb import DuckDBPyConnection
from sources.shared.lookup import LookupManager
from functools import lru_cache


class BloodHoundLookup(LookupManager):

    def __init__(self, client: DuckDBPyConnection, schema: str = "bloodhound_api"):
        super().__init__(client, schema)
        self.schema = schema
        self.client = client

    @lru_cache
    def find_asset(self, hostname: str) -> str | None:
        return self._find_single_object(
            f"""SELECT
                object_id
            FROM {self.schema}.nodes_api
            WHERE properties.name = ?;""",
            [hostname],
        )

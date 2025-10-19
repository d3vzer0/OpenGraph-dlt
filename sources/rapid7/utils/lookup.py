from duckdb import DuckDBPyConnection
from functools import lru_cache


class LookupManager:

    def __init__(self, client: DuckDBPyConnection, directory: str = "./output"):
        self.directory = directory
        self.schema = "bloodhound_lookup.bloodhound_staging"
        self.client = client

    def _find_object_id(self, *args) -> str:
        self.client.execute(*args)
        result = self.client.fetchone()
        return str(result[0]) if result else ""

    @lru_cache
    def find_asset(self, hostname: str):
        return self._find_object_id(
            f"""SELECT 
                properties.objectid
            FROM {self.schema}.node_kinds
            WHERE properties.name = ?;""",
            [hostname],
        )

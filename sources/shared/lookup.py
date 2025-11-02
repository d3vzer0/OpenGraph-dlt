from duckdb import DuckDBPyConnection
from functools import lru_cache


class LookupManager:
    def __init__(self, client: DuckDBPyConnection, schema: str):
        self.schema = schema
        self.client = client

    @lru_cache
    def _find_all_objects(self, *args) -> list:
        self.client.execute(*args)
        results = self.client.fetchall()
        return results

    @lru_cache
    def _find_single_object(self, *args) -> str | None:
        self.client.execute(*args)
        result = self.client.fetchone()
        return str(result[0]) if result else None

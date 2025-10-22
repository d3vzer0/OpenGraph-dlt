from duckdb import DuckDBPyConnection
from typing import Dict, Any
from functools import lru_cache
import json
import os


class LookupManager:

    def __init__(self, client: DuckDBPyConnection, directory: str = "./output"):
        self.directory = directory
        self.schema = "k8s_lookup.main"
        self.client = client

    def _load_json(self, filename: str) -> Dict[str, Any]:
        filepath = os.path.join(self.directory, filename)
        if not os.path.exists(filepath):
            return {}
        with open(filepath, "r") as f:
            return json.load(f)

    def _find_uid(self, *args) -> str:
        self.client.execute(*args)
        result = self.client.fetchone()
        return str(result[0]) if result else ""

    def _find_resources(self, *args) -> list:
        self.client.execute(*args)
        results = self.client.fetchall()
        return results

    @lru_cache
    def allowed_system_resources(self, resource_type: str) -> list[tuple]:
        return self._find_resources(
            f"""SELECT 
                name,
                kind,
                definition,
                singular_name
            FROM {self.schema}.resources_with_definitions
            WHERE definition GLOB ?;""",
            [resource_type],
        )

    @lru_cache
    def allowed_namespaced_resources(
        self, resource_type: str, namespace: str
    ) -> list[tuple]:
        results = self._find_resources(
            f"""SELECT 
                name,
                kind,
                namespace,
                singular_name,
                definition
            FROM {self.schema}.resources_with_definitions
            WHERE definition GLOB ? AND namespace = ?;""",
            [resource_type, namespace],
        )
        return results

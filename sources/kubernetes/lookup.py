from duckdb import DuckDBPyConnection
from typing import Dict, Any
from functools import lru_cache
from sources.shared.lookup import LookupManager
import json
import os


class KubernetesLookup(LookupManager):

    def __init__(self, client: DuckDBPyConnection, schema: str = "kubernetes"):
        super().__init__(client, schema)
        self.schema = schema
        self.client = client

    @lru_cache
    def allowed_system_resources(self, resource_type: str):
        return self._find_all_objects(
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
        results = self._find_all_objects(
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

from duckdb import DuckDBPyConnection


class LookupManager:

    def __init__(self, client: DuckDBPyConnection, directory: str = "./output"):
        self.directory = directory
        self.schema = "bloodhound_lookup.bloodhound_staging"
        self.client = client

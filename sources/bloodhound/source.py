from dlt.sources.filesystem import filesystem as filesystemsource, read_jsonl, readers
from destinations.opengraph.client import BloodHound
from .models.node import BloodHoundNode
from typing import Iterator
import dlt


@dlt.source()
def bloodhound_source(
    token_key: str = dlt.secrets.value,
    token_id: str = dlt.secrets.value,
    host: str = dlt.secrets.value,
    limit: int = 500,
):
    client: BloodHound = BloodHound(token_key, token_id, host)

    def iterate_results(node_type: str) -> Iterator[dict]:
        skip = 0
        while True:
            query = f"MATCH (n:{node_type}) RETURN n ORDER BY n.objectId SKIP {skip} LIMIT {limit}"
            response = client.query(query=query, include_properties=True)
            if response.status_code != 200:
                break

            response_json = response.json()
            nodes = response_json["data"]["nodes"]
            for node in nodes.values():
                yield node

            skip += len(nodes)

    @dlt.resource(columns=BloodHoundNode, table_name="nodes", parallelized=True)
    def computers() -> Iterator[dict]:
        for computer in iterate_results("Computer"):
            yield computer

    @dlt.resource(columns=BloodHoundNode, table_name="nodes", parallelized=True)
    def users() -> Iterator[dict]:
        for computer in iterate_results("User"):
            yield computer

    @dlt.resource(columns=BloodHoundNode, table_name="nodes", parallelized=True)
    def base() -> Iterator[dict]:
        for base_node in iterate_results("Base"):
            yield base_node

    return (computers, users, base)

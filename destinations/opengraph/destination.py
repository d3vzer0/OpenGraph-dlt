import dlt
from typing import Iterator, Optional
from dlt.common.typing import TDataItems
from dlt.common.schema import TTableSchema
from destinations.opengraph.models.graph import Graph, GraphEntries, MetaData
from .client import BloodHound
from pathlib import Path
import json
import uuid


# @dlt.destination(batch_size=1000)
# def bloodhound(
#     items: TDataItems,
#     table: TTableSchema,
#     api_url: str = dlt.config.value,
#     token_key: str = dlt.secrets.value,
#     token_id: str = dlt.secrets.value,
# ):
#     client = BloodHound(token_key, token_id, api_url)
#     # print(items)


@dlt.destination(batch_size=10)
def opengraph_file(items, table, output_path="./output"):
    output_dir = Path(output_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    merged = GraphEntries(nodes=[], edges=[])

    for raw_item in items:
        graph = Graph.model_validate(raw_item)
        merged.nodes.extend(graph.graph.nodes)
        merged.edges.extend(graph.graph.edges)

    aggregated = Graph(graph=merged)
    file_name = f"{table['name']}-{str(uuid.uuid4())}.json"
    file_path = output_dir / file_name
    with file_path.open("w", encoding="utf-8") as fh:
        json.dump(aggregated.model_dump(mode="json"), fh, indent=2)

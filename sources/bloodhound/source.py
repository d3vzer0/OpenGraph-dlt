from dlt.sources.filesystem import filesystem as filesystemsource, read_jsonl, readers
from destinations.opengraph.client import BloodHound
from .models.node import BloodHoundNode
from typing import Iterator
from FlagEmbedding import BGEM3FlagModel
import torch
import pyarrow as pa
import numpy as np
import dlt
import duckdb
import os


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


@dlt.source()
def bloodhound_embeddings(
    lookup_path: str = "lookup.duckdb",
    db_batch_size: int = 10000,
    model_batch_size: int = 128,
    embedding_model: str = "BAAI/bge-m3",
):
    conn = duckdb.connect(lookup_path)
    # conn.execute("LOAD vss;")
    # conn.execute(
    #     "SET GLOBAL hnsw_enable_experimental_persistence = true;",
    # )
    device = "cpu"
    if torch.backends.mps.is_available():
        device = "mps"

    os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "true"
    model = BGEM3FlagModel(embedding_model, use_fp16=True, device=device)

    @dlt.resource(
        name="embeddings",
        table_name="embeddings",
        write_disposition="merge",
        primary_key="object_id",
        columns={
            "object_id": {"data_type": "text"},
            "embedding": {"data_type": "json"},
        },
    )
    def embeddings():
        reader = conn.execute(
            """
            SELECT
                n._dlt_id,
                n.object_id,
                n.kind || ' ' || n.label || ' ' || CAST(n.properties AS VARCHAR) as embedding_text
            FROM bloodhound_api.nodes_api AS n
            LEFT JOIN bloodhound_api.embeddings AS e
                ON e.object_id = n.object_id
            WHERE e.object_id IS NULL
            """
        ).fetch_record_batch(db_batch_size)

        for batch in reader:
            vectors = model.encode(
                batch["embedding_text"].to_pylist(), batch_size=model_batch_size
            )["dense_vecs"].astype(np.float32)

            for idx, vec in enumerate(vectors):
                yield {
                    "object_id": batch["object_id"][idx].as_py(),
                    "embedding": vec.tolist(),
                }
        conn.close()

    return embeddings

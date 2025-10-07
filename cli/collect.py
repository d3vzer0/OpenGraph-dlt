import typer
import dlt
from sources.kubernetes.source import (
    kubernetes_resources,
)
from dlt.sources.filesystem import readers
from dlt.destinations import filesystem
from typing import Annotated
from pathlib import Path

collect = typer.Typer()

OutputPath = Annotated[
    Path,
    typer.Argument(
        exists=True, file_okay=True, dir_okay=True, readable=True, resolve_path=True
    ),
]


@collect.command()
def kubernetes(output_path: OutputPath):
    dest = filesystem(
        bucket_url=output_path,
    )

    pipeline = dlt.pipeline(
        pipeline_name="k8s_stage",
        destination=dest,
        dataset_name="kubernetes",
        progress="enlighten",
    )
    pipeline.run(
        kubernetes_resources(
            kube_config="~/.kube/config",
            cluster="colima",
        ),
    )

    def extract_values(item):
        if "metadata" in item:
            value = {
                "kind": item["kind"],
                "name": item["metadata"]["name"],
                "namespace": item["metadata"].get("namespace"),
            }
            return value

    lookup = dlt.pipeline(
        pipeline_name="k8s_lookup",
        destination="duckdb",
        dataset_name="kubernetes",
        progress="enlighten",
    )

    met_files = (
        readers(bucket_url="./output", file_glob="**/*.jsonl.gz")
        .read_jsonl()
        .with_name("resources")
    )
    transformed_data = met_files.add_map(extract_values)
    lookup.run(
        transformed_data,
        columns={
            "kind": {"data_type": "text"},
            "name": {"data_type": "text"},
            "namespace": {"data_type": "text"},
        },
    )

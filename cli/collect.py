import typer
import dlt
from sources.kubernetes.source import (
    kubernetes_resources,
)
from sources.aws.source import (
    aws_resources,
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
def aws(output_path: OutputPath):
    dest = filesystem(
        bucket_url=str(output_path),
    )

    # pipeline = dlt.pipeline(
    #     pipeline_name="aws_stage",
    #     destination=dest,
    #     dataset_name="aws",
    #     progress="enlighten",
    # )

    lookup = dlt.pipeline(
        pipeline_name="aws_lookup",
        destination="duckdb",
        dataset_name="aws",
        progress="enlighten",
    )

    lookup.run(aws_resources().with_resources("resources"))

    # pipeline.run(
    #     aws_resources().with_resources("resources"),
    #     write_disposition="replace",
    # )


@collect.command()
def kubernetes(output_path: OutputPath):
    dest = filesystem(
        bucket_url=str(output_path),
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
        write_disposition="replace",
    )

    lookup = dlt.pipeline(
        pipeline_name="k8s_lookup",
        destination="duckdb",
        dataset_name="kubernetes",
        progress="enlighten",
    )

    resource_files = (
        (
            readers(bucket_url="./output", file_glob="**/*.jsonl.gz")
            .read_jsonl()
            .with_name("resources")
        )
        .add_filter(lambda item: item.get("metadata"))
        .add_map(
            lambda item, meta=None: {
                "kind": item["kind"],
                "name": item["metadata"]["name"],
                "namespace": item["metadata"].get("namespace"),
            }
        )
    )
    lookup.run(
        resource_files,
        columns={
            "kind": {"data_type": "text"},
            "name": {"data_type": "text"},
            "namespace": {"data_type": "text"},
        },
        write_disposition="replace",
    )

    resource_definition_files = (
        readers(
            bucket_url="./output", file_glob="**/resource_definitions/**/*.jsonl.gz"
        )
        .read_jsonl()
        .with_name("resource_definitions")
        .add_map(
            lambda item: {
                "kind": item["kind"],
                "name": item["name"],
                "namespaced": item["namespaced"],
                "singular_name": item["singular_name"],
                "group": item["group"],
            }
        )
    )
    lookup.run(
        resource_definition_files,
        columns={
            "kind": {"data_type": "text"},
            "name": {"data_type": "text"},
            "namespaced": {"data_type": "bool"},
            "singular_name": {"data_type": "text"},
            "group": {"data_type": "text"},
        },
        write_disposition="replace",
    )

    dbt = dlt.dbt.package(
        lookup,
        "sources/kubernetes/dbt",
    )
    dbt.run_all()

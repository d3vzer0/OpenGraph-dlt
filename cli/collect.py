import typer
import dlt
from sources.kubernetes.source import kubernetes_resources
from sources.aws.source import aws_resources
from sources.rapid7.source import rapid7_source
from sources.bloodhound.source import bloodhound_source, bloodhound_embeddings
from sources.resource_files.source import resource_files
from dlt.sources.filesystem import readers
from dlt.destinations import filesystem
from typing import Annotated
from pathlib import Path

from kubernetes import config

from dlt.sources.sql_database import sql_database
from typing import List, Annotated

collect = typer.Typer()

OutputPath = Annotated[
    Path,
    typer.Argument(
        exists=True, file_okay=True, dir_okay=True, readable=True, resolve_path=True
    ),
]


@collect.command()
def aws_lookup(input_path: Path = Path("./output/aws")):
    duckdb_dest = dlt.destinations.duckdb("lookup.duckdb")
    lookup = dlt.pipeline(
        pipeline_name="duckdb_lookup",
        destination=duckdb_dest,
        dataset_name="aws",
        progress="enlighten",
    )
    lookup.run(
        resource_files(
            input_path,
            resource_names=["resources", "users", "groups", "roles"],
        )
    )

    dbt = dlt.dbt.package(
        lookup,
        "sources/aws/dbt",
    )
    dbt.run_all()


@collect.command()
def aws(
    output_path: OutputPath,
    lookup: Annotated[
        bool, typer.Option(help="Generate lookup database afterwards")
    ] = True,
):
    dest = filesystem(
        bucket_url=str(output_path),
    )

    pipeline = dlt.pipeline(
        pipeline_name="aws_collector",
        destination=dest,
        dataset_name="aws",
        progress="enlighten",
    )

    pipeline.run(
        aws_resources(), write_disposition="replace", loader_file_format="parquet"
    )

    if lookup:
        aws_lookup(Path(f"{output_path}/aws"))


@collect.command()
def kubernetes(output_path: OutputPath):

    contexts, active = config.list_kube_config_contexts()
    cluster_name = active["context"]["cluster"]

    dest = filesystem(
        bucket_url=str(output_path),
    )

    pipeline = dlt.pipeline(
        pipeline_name="kube_collection",
        destination=dest,
        dataset_name="kubernetes",
        progress="enlighten",
    )

    pipeline.run(
        kubernetes_resources(
            kube_config="~/.kube/config",
            cluster=cluster_name,
        ),
        write_disposition="replace",
        loader_file_format="parquet",
    )

    duckdb_dest = dlt.destinations.duckdb("lookup.duckdb")
    lookup = dlt.pipeline(
        pipeline_name="k8s_lookup",
        destination=duckdb_dest,
        dataset_name="kubernetes",
        progress="enlighten",
    )

    resource_files = (
        (
            readers(
                bucket_url=f"{str(output_path)}/kubernetes", file_glob="**/*.jsonl.gz"
            )
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
            bucket_url=f"{str(output_path)}/kubernetes",
            file_glob="**/resource_definitions/**/*.jsonl.gz",
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


@collect.command()
def bloodhound(filters: Annotated[list[str], typer.Argument] = []):

    duckdb_dest = dlt.destinations.duckdb("lookup.duckdb")
    pipeline = dlt.pipeline(
        pipeline_name="bloodhound_lookup",
        destination=duckdb_dest,
        dataset_name="bloodhound_pg",
        progress="enlighten",
    )

    source = sql_database().with_resources("node", "kind", "edge")
    pipeline.run(source, write_disposition="replace")
    dbt = dlt.dbt.package(
        pipeline,
        "sources/bloodhound/dbt",
    )
    dbt.run_all(run_params=("--fail-fast", "--select", "staging_pg"))


@collect.command()
def bloodhound_vector(
    input_path: Path = Path("lookup.duckdb"),
    bsize: Annotated[
        int, typer.Option(help="Batch size for fetching DB entries")
    ] = 10000,
    msize: Annotated[
        int,
        typer.Option(help="Batch size for model inferenc when generating embeddings"),
    ] = 128,
):
    duckdb_dest = dlt.destinations.duckdb(
        "lookup.duckdb",
    )
    pipeline = dlt.pipeline(
        pipeline_name="bloodhound_embeddings",
        destination=duckdb_dest,
        dataset_name="bloodhound_api",
        progress="enlighten",
    )

    pipeline.run(
        bloodhound_embeddings(
            lookup_path=str(input_path), db_batch_size=bsize, model_batch_size=msize
        ),
        write_disposition="replace",
    )
    # dbt = dlt.dbt.package(pipeline, "sources/bloodhound/dbt")
    # dbt.run_all(run_params=("--fail-fast", "--select", "embeddings_api"))


@collect.command()
def bloodhound_api(
    limit: int = 500, nodes: Annotated[list[str], typer.Argument] = ["computers"]
):
    duckdb_dest = dlt.destinations.duckdb("lookup.duckdb")
    pipeline = dlt.pipeline(
        pipeline_name="bloodhound_lookup",
        destination=duckdb_dest,
        dataset_name="bloodhound_api",
        progress="enlighten",
    )

    pipeline.run(
        bloodhound_source(limit=limit).with_resources(*nodes),
        write_disposition="replace",
    )
    dbt = dlt.dbt.package(pipeline, "sources/bloodhound/dbt")
    dbt.run_all(run_params=("--fail-fast", "--select", "staging_api"))


@collect.command()
def rapid7(
    output_path: OutputPath,
    insecure: Annotated[
        bool, typer.Option(help="Don't verify Rapid7 server certificate")
    ] = False,
):
    dest = filesystem(
        bucket_url=str(output_path),
    )

    pipeline = dlt.pipeline(
        pipeline_name="rapid7_collector",
        destination=dest,
        dataset_name="rapid7",
        progress="enlighten",
    )

    pipeline.run(
        rapid7_source(insecure=insecure),
        loader_file_format="parquet",
    )

from dlt.destinations import filesystem
from typing import Annotated
from pathlib import Path
from typing import List
from dlt.sources.sql_database import sql_database
from opengraph_dlt.cli.preproc import (
    kubernetes as preproc_kubernetes,
    aws as preproc_aws,
)
import typer
import dlt

collect = typer.Typer()

OutputPath = Annotated[
    Path,
    typer.Argument(
        exists=True, file_okay=True, dir_okay=True, readable=True, resolve_path=True
    ),
]


@collect.command()
def aws(
    output_path: OutputPath,
    resources: Annotated[List[str], typer.Argument()] = [],
    profile: Annotated[
        str,
        typer.Option(
            help="Which AWS profile to use. If none specified, the default is used"
        ),
    ] = "default",
    lookup: Annotated[
        bool, typer.Option(help="Generate database for lookups/matching afterwards")
    ] = True,
):

    from opengraph_dlt.sources.aws.source import aws_resources

    dest = filesystem(
        bucket_url=str(output_path),
    )

    pipeline = dlt.pipeline(
        pipeline_name="aws_collector",
        destination=dest,
        dataset_name="aws",
        progress="enlighten",
    )

    all_resources = aws_resources(profile_name=profile)
    if resources:
        all_resources = all_resources.with_resources(*resources)

    pipeline.run(
        all_resources,
        write_disposition="replace",
    )
    if lookup:
        preproc_aws(output_path / "aws")


@collect.command()
def kubernetes(
    output_path: OutputPath,
    lookup: Annotated[
        bool, typer.Option(help="Generate database for lookups/matching afterwards")
    ] = True,
):
    from opengraph_dlt.sources.kubernetes.source import kubernetes_resources
    from kubernetes import config

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
        loader_file_format="jsonl",
    )

    if lookup:
        preproc_kubernetes(output_path / "kubernetes")


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
        "opengraph_dlt/sources/bloodhound/dbt",
    )
    dbt.run_all(run_params=("--fail-fast", "--select", "staging_pg"))


@collect.command()
def okta(output_path: OutputPath):
    from opengraph_dlt.sources.okta.source import okta_source

    dest = filesystem(
        bucket_url=str(output_path),
    )

    pipeline = dlt.pipeline(
        pipeline_name="okta_collection",
        destination=dest,
        dataset_name="okta",
        progress="enlighten",
    )

    pipeline.run(
        okta_source(),
        write_disposition="replace",
        loader_file_format="jsonl",
    )


# @collect.command()
# def bloodhound_vector(
#     input_path: Path = Path("lookup.duckdb"),
#     bsize: Annotated[
#         int, typer.Option(help="Batch size for fetching DB entries")
#     ] = 10000,
#     msize: Annotated[
#         int,
#         typer.Option(help="Batch size for model inferenc when generating embeddings"),
#     ] = 128,
# ):
#     duckdb_dest = dlt.destinations.duckdb(
#         "lookup.duckdb",
#     )
#     pipeline = dlt.pipeline(
#         pipeline_name="bloodhound_embeddings",
#         destination=duckdb_dest,
#         dataset_name="bloodhound_api",
#         progress="enlighten",
#     )

#     pipeline.run(
#         bloodhound_embeddings(
#             lookup_path=str(input_path), db_batch_size=bsize, model_batch_size=msize
#         ),
#         write_disposition="replace",
#     )
#     # dbt = dlt.dbt.package(pipeline, "sources/bloodhound/dbt")
#     # dbt.run_all(run_params=("--fail-fast", "--select", "embeddings_api"))


@collect.command()
def bloodhound_api(
    limit: int = 500, nodes: Annotated[list[str], typer.Argument] = ["computers"]
):
    from opengraph_dlt.sources.bloodhound.source import (
        bloodhound_source,
    )

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
    from opengraph_dlt.sources.rapid7.source import rapid7_source

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
        # loader_file_format="parquet",
    )

from opengraph_dlt.sources.resource_files.source import resource_files
from dlt.sources.filesystem import readers, filesystem, read_jsonl
from typing import Annotated
from pathlib import Path
import typer
import dlt

PACKAGE_ROOT = Path(__file__).resolve().parents[1]

preprocess = typer.Typer()

OutputPath = Annotated[
    Path,
    typer.Argument(
        exists=True, file_okay=True, dir_okay=True, readable=True, resolve_path=True
    ),
]


@preprocess.command()
def aws(input_path: Path):
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
            resource_names=[
                "resources",
                "users",
                "groups",
                "roles",
                "policies",
                "policy_attachments",
            ],
        ),
        write_disposition="replace",
    )

    dbt = dlt.dbt.package(lookup, str(PACKAGE_ROOT.joinpath("sources", "aws", "dbt")))
    dbt.run_all()


@preprocess.command()
def kubernetes(input_path: Path):

    duckdb_dest = dlt.destinations.duckdb("lookup.duckdb")
    lookup = dlt.pipeline(
        pipeline_name="k8s_lookup",
        destination=duckdb_dest,
        dataset_name="kubernetes",
        progress="enlighten",
    )

    local_resource_files = (
        (
            readers(bucket_url=f"{str(input_path)}", file_glob="**/*.jsonl.gz")
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
        local_resource_files,
        columns={
            "kind": {"data_type": "text"},
            "name": {"data_type": "text"},
            "namespace": {"data_type": "text"},
        },
        write_disposition="replace",
    )

    resource_definition_files = (
        readers(
            bucket_url=f"{str(input_path)}",
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
        lookup, str(PACKAGE_ROOT.joinpath("sources", "kubernetes", "dbt"))
    )
    dbt.run_all()

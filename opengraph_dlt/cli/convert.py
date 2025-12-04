from opengraph_dlt.destinations.opengraph.destination import opengraph_file
from opengraph_dlt.sources.bloodhound.lookup import BloodHoundLookup
from dlt.destinations import filesystem
from dlt.sources.filesystem import filesystem as fs_source, read_jsonl

from typing import Annotated
from pathlib import Path
from kubernetes import config
import typer
import dlt
import duckdb

convert = typer.Typer(pretty_exceptions_enable=False)

OutputPath = Annotated[
    Path,
    typer.Argument(
        exists=True, file_okay=True, dir_okay=True, readable=True, resolve_path=True
    ),
]

InputPath = Annotated[
    Path,
    typer.Argument(
        exists=True, file_okay=True, dir_okay=True, readable=True, resolve_path=True
    ),
]


@convert.command()
def aws(
    ctx: typer.Context, input_path: InputPath, output_path: OutputPath = Path("./graph")
):
    from opengraph_dlt.sources.aws.convert import aws_opengraph
    from opengraph_dlt.sources.aws.lookup import AWSLookup

    client = duckdb.connect("lookup.duckdb", read_only=True)
    lookup = AWSLookup(client)

    pipeline = dlt.pipeline(
        pipeline_name="aws_opengraph_convert_2",
        destination=opengraph_file(output_path=str(output_path)),
        progress="enlighten",
    )

    pipeline.run(
        aws_opengraph(lookup=lookup, bucket_url=str(input_path), chunk_size=10)
    )


@convert.command()
def kubernetes(input_path: InputPath, output_path: OutputPath = Path("./graph")):
    from opengraph_dlt.sources.kubernetes.convert import kubernetes_opengraph
    from opengraph_dlt.sources.kubernetes.lookup import KubernetesLookup

    contexts, active = config.list_kube_config_contexts()
    cluster_name = active["context"]["cluster"]
    client = duckdb.connect("lookup.duckdb", read_only=True)
    lookup = KubernetesLookup(client)
    pipeline = dlt.pipeline(
        pipeline_name="k8s_opengraph_convert",
        destination=opengraph_file(output_path=str(output_path)),
        progress="enlighten",
    )
    pipeline.run(
        kubernetes_opengraph(
            cluster=cluster_name,
            lookup=lookup,
            bucket_url=str(input_path),
            chunk_size=1000,
        )
    )


@convert.command()
def rapid7(input_path: InputPath, output_path: OutputPath = Path("./graph")):
    from opengraph_dlt.sources.rapid7.source import rapid7_opengraph

    client = duckdb.connect("lookup.duckdb", read_only=True)
    lookup = BloodHoundLookup(client)
    pipeline = dlt.pipeline(
        pipeline_name="rapid7_opengraph_convert",
        destination=opengraph_file(output_path=str(output_path)),
        progress="enlighten",
    )
    pipeline.run(rapid7_opengraph(lookup=lookup, bucket_url=str(input_path)))


@convert.command()
def eks(output_path: OutputPath = Path("./graph")):
    from opengraph_dlt.sources.kubernetes.collect import kubernetes_eks_opengraph
    from opengraph_dlt.sources.kubernetes.lookup import KubernetesLookup

    contexts, active = config.list_kube_config_contexts()
    cluster_name = active["context"]["cluster"]

    client = duckdb.connect("lookup.duckdb", read_only=True)
    lookup = KubernetesLookup(client)

    pipeline = dlt.pipeline(
        pipeline_name="k8s_opengraph_eks_convert",
        destination=opengraph_file(output_path=str(output_path)),
        progress="enlighten",
    )

    pipeline.run(kubernetes_eks_opengraph(cluster=cluster_name, lookup=lookup))

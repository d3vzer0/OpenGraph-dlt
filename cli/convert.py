import typer
import dlt
import duckdb
from sources.kubernetes.source import (
    kubernetes_opengraph,
    kubernetes_eks_opengraph,
)

from sources.aws.source import aws_opengraph
from sources.rapid7.source import rapid7_opengraph

# from destinations.opengraph.client import BloodHound
from destinations.opengraph.destination import opengraph_file
from sources.kubernetes.lookup import KubernetesLookup
from sources.aws.lookup import AWSLookup
from sources.bloodhound.lookup import BloodHoundLookup
from typing import Annotated
from pathlib import Path

from kubernetes import config

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
    client = duckdb.connect("lookup.duckdb", read_only=True)
    lookup = AWSLookup(client)

    pipeline = dlt.pipeline(
        pipeline_name="aws_opengraph_convert",
        destination=opengraph_file(output_path=str(output_path)),
        progress="enlighten",
    )
    pipeline.run(aws_opengraph(lookup=lookup, bucket_url=str(input_path)))


@convert.command()
def kubernetes(input_path: InputPath, output_path: OutputPath = Path("./graph")):
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
            cluster=cluster_name, lookup=lookup, bucket_url=str(input_path)
        )
    )


@convert.command()
def rapid7(input_path: InputPath, output_path: OutputPath = Path("./graph")):
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

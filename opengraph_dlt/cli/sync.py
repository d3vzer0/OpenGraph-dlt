import typer
import dlt
import duckdb
from opengraph_dlt.sources.kubernetes.source import (
    kubernetes_opengraph,
    kubernetes_eks_opengraph,
)

from opengraph_dlt.sources.aws.source import aws_opengraph
from opengraph_dlt.sources.rapid7.source import rapid7_opengraph
from opengraph_dlt.destinations.opengraph.client import BloodHound
from opengraph_dlt.destinations.opengraph.destination import bloodhound
from opengraph_dlt.sources.kubernetes.lookup import KubernetesLookup
from opengraph_dlt.sources.aws.lookup import AWSLookup
from opengraph_dlt.sources.bloodhound.lookup import BloodHoundLookup
from typing import Annotated
from dataclasses import dataclass
from pathlib import Path

from kubernetes import config

sync = typer.Typer(pretty_exceptions_enable=False)

InputPath = Annotated[
    Path,
    typer.Argument(
        exists=True, file_okay=True, dir_okay=True, readable=True, resolve_path=True
    ),
]


@sync.command()
def aws(ctx: typer.Context, input_path: InputPath):
    client = duckdb.connect("lookup.duckdb", read_only=True)
    lookup = AWSLookup(client)

    pipeline = dlt.pipeline(
        pipeline_name="aws_opengraph_sync",
        destination=bloodhound(),
        progress="enlighten",
    )
    pipeline.run(aws_opengraph(lookup=lookup, bucket_url=str(input_path)))


@sync.command()
def kubernetes(input_path: InputPath):
    contexts, active = config.list_kube_config_contexts()
    cluster_name = active["context"]["cluster"]

    client = duckdb.connect("lookup.duckdb", read_only=True)
    lookup = KubernetesLookup(client)
    pipeline = dlt.pipeline(
        pipeline_name="k8s_opengraph_synct",
        destination=bloodhound(),
        progress="enlighten",
    )
    pipeline.run(
        kubernetes_opengraph(
            cluster=cluster_name, lookup=lookup, bucket_url=str(input_path)
        )
    )


@sync.command()
def rapid7(input_path: InputPath):
    client = duckdb.connect("lookup.duckdb", read_only=True)
    lookup = BloodHoundLookup(client)
    pipeline = dlt.pipeline(
        pipeline_name="rapid7_opengraph_sync",
        destination=bloodhound(),
        progress="enlighten",
    )
    pipeline.run(rapid7_opengraph(lookup=lookup, bucket_url=str(input_path)))


@sync.command()
def eks():
    contexts, active = config.list_kube_config_contexts()
    cluster_name = active["context"]["cluster"]

    client = duckdb.connect("lookup.duckdb", read_only=True)
    lookup = KubernetesLookup(client)

    pipeline = dlt.pipeline(
        pipeline_name="k8s_opengraph_eks_sync",
        destination=bloodhound(),
        progress="enlighten",
    )

    pipeline.run(kubernetes_eks_opengraph(cluster=cluster_name, lookup=lookup))

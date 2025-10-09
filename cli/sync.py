import typer
import dlt
import duckdb
from sources.kubernetes.source import (
    kubernetes_opengraph,
    kubernetes_fs,
)

from sources.aws.source import aws_fs, aws_opengraph

from destinations.opengraph.client import BloodHound
from destinations.opengraph.destination import opengraph_file
from sources.kubernetes.utils.lookup import LookupManager
from sources.aws.utils.lookup import LookupManager as AWSLookupManager

from typing import Annotated
from dataclasses import dataclass
from pathlib import Path


sync = typer.Typer(pretty_exceptions_enable=False)
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


@dataclass
class SyncOptions:
    session: BloodHound
    job_id: int | None = None


@dataclass
class ConvertOptions:
    output: Path


# @convert.callback()
# def convert_callback(
#     ctx: typer.Context,
#     output: Annotated[
#         Path,
#         typer.Option(
#             exists=True,
#             file_okay=False,
#             dir_okay=True,
#             writable=False,
#             readable=True,
#             resolve_path=True,
#         ),
#     ],
# ):
#     ctx.obj = ConvertOptions(output=output)


@convert.command()
def aws(input_path: InputPath, output_path: OutputPath):
    client = duckdb.connect("aws_lookup.duckdb", read_only=True)
    lookup = AWSLookupManager(client)
    fs_source = aws_fs(str(input_path))

    pipeline = dlt.pipeline(
        pipeline_name="aws_opengraph_convert",
        destination=opengraph_file(output_path="./graph"),
        progress="enlighten",
    )
    pipeline.run(aws_opengraph(lookup=lookup, raw_source=fs_source))


# @sync.command()
@convert.command()
def kubernetes(input_path: InputPath, output_path: OutputPath):
    client = duckdb.connect("k8s_lookup.duckdb", read_only=True)
    lookup = LookupManager(client)
    fs_source = kubernetes_fs("./output/kubernetes")
    pipeline = dlt.pipeline(
        pipeline_name="k8s_opengraph_convert",
        destination=opengraph_file(output_path="./graph"),
        progress="enlighten",
    )
    pipeline.run(
        kubernetes_opengraph(cluster="colima", lookup=lookup, raw_source=fs_source)
    )

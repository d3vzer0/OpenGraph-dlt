import typer
import dlt
import duckdb
from sources.kubernetes.source import (
    kubernetes_opengraph,
    kubernetes_fs,
)

from destinations.opengraph.client import BloodHound
from destinations.opengraph.destination import opengraph_file
from sources.kubernetes.utils.lookup import LookupManager
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

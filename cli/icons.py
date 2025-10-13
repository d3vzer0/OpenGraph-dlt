import typer
from sources.kubernetes.icons import (
    KUBE_ICONS,
)
from sources.aws.icons import (
    AWS_ICONS,
)
from destinations.opengraph.client import BloodHound
from pydantic import BaseModel
from dataclasses import dataclass
from typing_extensions import Annotated

icons = typer.Typer()


class CustomNodeIcon(BaseModel):
    type: str
    name: str
    color: str


class CustomNodeType(BaseModel):
    icon: CustomNodeIcon


class CustomNode(BaseModel):
    custom_types: dict[str, CustomNodeType]


@dataclass
class SyncOptions:
    session: BloodHound


@icons.callback()
def sync_callback(
    ctx: typer.Context,
    bhe_uri: Annotated[str, typer.Option(envvar="BHE_URI")],
    token_id: Annotated[str, typer.Option(envvar="BHE_API_ID")],
    token_key: Annotated[str, typer.Option(envvar="BHE_API_KEY")],
):
    session = BloodHound(token_id=token_id, token_key=token_key, bhe_uri=bhe_uri)
    ctx.obj = SyncOptions(session)


def sync_icons(client: BloodHound, icons: dict, color: str = "#FFFFFF"):
    for node_name, icon_name in icons.items():
        node_icon = CustomNodeIcon(type="font-awesome", name=icon_name, color=color)
        node_type = CustomNodeType(icon=node_icon)
        custom_type = {"custom_types": {node_name: node_type}}
        custom = CustomNode(**custom_type)
        client.custom_node(custom.model_dump_json())


@icons.command()
def aws(ctx: typer.Context, color: str = "#EE7D0C"):
    typer.echo("Syncing AWS icons")
    sync_icons(ctx.obj.session, AWS_ICONS, color=color)


@icons.command()
def kubernetes(ctx: typer.Context, color: str = "#0077FF"):
    typer.echo("Syncing Kube icons")
    sync_icons(ctx.obj.session, KUBE_ICONS, color=color)

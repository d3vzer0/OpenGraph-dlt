import typer

from opengraph_dlt.cli.sync import sync
from opengraph_dlt.cli.convert import convert
from opengraph_dlt.cli.icons import icons
from opengraph_dlt.cli.collect import collect
from opengraph_dlt.cli.preproc import preprocess

app = typer.Typer(pretty_exceptions_enable=False)
app.add_typer(sync, name="sync")
app.add_typer(convert, name="convert")
app.add_typer(collect, name="collect")
app.add_typer(preprocess, name="preprocess")
app.add_typer(icons, name="icons")

if __name__ == "__main__":
    app()

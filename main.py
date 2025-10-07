import typer
from cli.sync import sync, convert
from cli.collect import collect

app = typer.Typer(pretty_exceptions_enable=False)
app.add_typer(sync, name="sync")
app.add_typer(convert, name="convert")
app.add_typer(collect, name="collect")

if __name__ == "__main__":
    app()

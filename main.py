import typer
import dlt
from destinations.opengraph.destination import opengraph
from sources.kubernetes.source import kubernetes_resources

app = typer.Typer(pretty_exceptions_enable=False)


@app.command()
def kubernetes():
    pipeline = dlt.pipeline(
        pipeline_name="k8s_ingest",
        destination=opengraph(api_url="https://api.opengraph.io"),
    )
    pipeline.run(
        kubernetes_resources(kube_config="~/.kube/config"), table_name="kubernetes"
    )


if __name__ == "__main__":
    app()

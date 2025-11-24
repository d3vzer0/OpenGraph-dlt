from typer.testing import CliRunner
from opengraph_dlt.cli import collect as collect_app

runner = CliRunner()


def test_collect_aws(tmp_path):
    args = ["aws", str(tmp_path)]
    runner.invoke(collect_app.collect, args)


def test_collect_kubernetes(tmp_path):
    args = ["kubernetes", str(tmp_path)]
    runner.invoke(collect_app.collect, args)


def test_collect_okta(tmp_path):
    args = ["okta", str(tmp_path)]
    runner.invoke(collect_app.collect, args)

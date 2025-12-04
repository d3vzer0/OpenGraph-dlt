from typer.testing import CliRunner
from opengraph_dlt.cli import convert as convert_app

runner = CliRunner()


def test_convert_aws(tmp_path):
    args = ["aws", "output/aws", str(tmp_path)]
    runner.invoke(convert_app.convert, args)


def test_convert_kubernetes(tmp_path):
    args = ["kubernetes", "output/kubernetes", str(tmp_path)]
    runner.invoke(convert_app.convert, args)


def test_convert_okta(tmp_path):
    args = ["okta", "output/okta", str(tmp_path)]
    runner.invoke(convert_app.convert, args)

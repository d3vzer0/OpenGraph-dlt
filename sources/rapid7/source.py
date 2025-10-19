from dlt.sources.helpers.rest_client.auth import HttpBasicAuth
from dlt.sources.helpers.rest_client import RESTClient
from .models.r7.asset import Asset
from .models.r7.vulnerability import (
    AssetVulnerability,
    AssetVulnerabilityNode,
    Vulnerability,
    VulnerabilityNode,
)
from .models.entries import Edge, EdgePath, EdgeProperties, Node as GraphNode
from .models.graph import GraphEntries, Graph
from sources.rapid7.utils.lookup import LookupManager
from dlt.sources.filesystem import filesystem as filesystemsource, read_jsonl
import dlt
import requests
import typer
import urllib3


@dlt.source
def rapid7_source(
    username: str = dlt.secrets.value,
    password: str = dlt.secrets.value,
    host: str = dlt.secrets.value,
    insecure: bool = False,
    # vuln_delta: int = 30,
):

    session = requests.Session()
    session.verify = False if insecure else True
    if insecure:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        typer.echo(
            "Warning: TLS verification is disabled. Make sure that this is expected."
        )

    # vulns_since = datetime.datetime.now() - datetime.timedelta(days=vuln_delta)
    # vulns_seen: set[str] = set()

    r7_client = RESTClient(
        base_url=host,
        auth=HttpBasicAuth(username, password),
        session=session,
    )

    @dlt.resource(name="assets", columns=Asset, table_name="assets")
    def assets():
        for page in r7_client.paginate("/api/3/assets", params={"size": 500}):
            for resource in page:
                yield resource

    @dlt.transformer(
        data_from=assets,
        columns=AssetVulnerability,
        table_name="asset_vulnerabilities",
        parallelized=True,
    )
    def asset_vulnerabilities(asset):
        asset_id = asset["id"]
        for page in r7_client.paginate(
            f"/api/3/assets/{asset_id}/vulnerabilities", params={"size": 500}
        ):
            for vulnerability in page:
                asset_details = {
                    "asset_id": asset_id,
                    "ip": asset["ip"],
                    "host_names": asset.get("hostNames"),
                    "host_name": asset.get("hostName"),
                }
                yield {**vulnerability, **asset_details}

    @dlt.transformer(
        data_from=asset_vulnerabilities,
        columns=Vulnerability,
        parallelized=True,
        table_name="vulnerabilities",
    )
    def vulnerabilities(vuln: dict):
        vuln_id = vuln["id"]
        details = r7_client.get(f"/api/3/vulnerabilities/{vuln_id}")
        yield details.json()

    # TODO: Decide if this will be more efficient compared to getting vulns per asset
    # @dlt.resource(
    #     name="vulnerabilities", columns=Vulnerability, table_name="vulnerabilities"
    # )
    # def vulnerabilities():
    #     for page in r7_client.paginate(
    #         "/api/3/vulnerabilities", params={"size": 500, "sort": "modified,DESC"}
    #     ):
    #         for resource in page:
    #             vulnerability = Vulnerability(**resource)
    #             if vulnerability.modified > vulns_since:
    #                 yield resource
    #             else:
    #                 return

    return assets, asset_vulnerabilities, vulnerabilities


@dlt.source(name="aws_opengraph")
def rapid7_opengraph(
    *,
    lookup: LookupManager,
    bucket_url: str = dlt.config.value,
):

    def json_resource(subdir: str):
        files = filesystemsource(
            bucket_url=bucket_url,
            file_glob=f"{subdir}/**/*.jsonl.gz",
        )
        return (files | read_jsonl()).with_name(f"{subdir}_fs")

    def build_graph(model_cls, resource: dict) -> Graph:
        node = model_cls.from_input(**resource)
        node._lookup = lookup
        entries = GraphEntries(
            nodes=[node],
            edges=[edge for edge in node.edges if edge],
        )
        return Graph(graph=entries)

    def build_graph_edges(model_cls, resource: dict) -> Graph:
        node = model_cls.from_input(**resource)
        node._lookup = lookup
        entries = GraphEntries(
            nodes=[],
            edges=[edge for edge in node.edges],
        )
        return Graph(graph=entries)

    @dlt.transformer(data_from=json_resource("vulnerabilities"), columns=Graph)
    def vulnerability_graph(vulnerabilities: list):
        for vulnerability in vulnerabilities:
            yield build_graph(VulnerabilityNode, vulnerability)

    @dlt.transformer(data_from=json_resource("asset_vulnerabilities"), columns=Graph)
    def asset_vulnerabilities_graph(vulnerabilities: list):
        for vulnerability in vulnerabilities:
            yield build_graph_edges(AssetVulnerabilityNode, vulnerability)

    return vulnerability_graph, asset_vulnerabilities_graph

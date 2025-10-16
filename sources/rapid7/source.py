from dlt.sources.helpers.rest_client.auth import HttpBasicAuth
from dlt.sources.helpers.rest_client import RESTClient
from .models.r7.asset import Asset
from .models.r7.vulnerability import AssetVulnerability, Vulnerability
import dlt
import requests
import datetime


@dlt.source
def rapid7_source(
    username: str = dlt.secrets.value,
    password: str = dlt.secrets.value,
    host: str = dlt.secrets.value,
    insecure: bool = False,
    vuln_delta: int = 30,
):

    vulns_since = datetime.datetime.now() - datetime.timedelta(days=vuln_delta)
    session = requests.Session()
    session.verify = False if insecure else True

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
        for vulnerability in r7_client.paginate(
            f"/api/3/assets/{asset_id}/vulnerabilities", params={"size": 500}
        ):
            yield vulnerability

    @dlt.resource(
        name="vulnerabilities", columns=Vulnerability, table_name="vulnerabilities"
    )
    def vulnerabilities():
        for page in r7_client.paginate(
            "/api/3/vulnerabilities", params={"size": 500, "sort": "modified,DESC"}
        ):
            for resource in page:
                vulnerability = Vulnerability(**resource)
                if vulnerability.modified > vulns_since:
                    yield resource
                else:
                    return

    return assets, asset_vulnerabilities, vulnerabilities

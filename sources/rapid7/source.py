from dlt.sources.rest_api import rest_api_resources
from dlt.sources.rest_api.typing import RESTAPIConfig
from dlt.sources.helpers.rest_client.auth import HttpBasicAuth
import dlt


@dlt.source
def rapid7_source(
    username: str = dlt.secrets.value,
    password: str = dlt.secrets.value,
    host: str = dlt.secrets.value,
):
    config: RESTAPIConfig = {
        "client": {
            "base_url": host,
            "auth": HttpBasicAuth(username, password),
        },
        "resource_defaults": {
            "primary_key": "id",
            "write_disposition": "merge",
            "endpoint": {
                "params": {
                    "per_page": 100,
                },
            },
        },
        "resources": [
            {
                "name": "assets",
                "endpoint": {
                    "path": "assets",
                },
            },
        ],
    }

    yield from rest_api_resources(config)

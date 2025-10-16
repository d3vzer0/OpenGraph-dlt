from dlt.sources.rest_api import rest_api_resources
from dlt.sources.rest_api.typing import RESTAPIConfig
from dlt.sources.helpers.rest_client.auth import HttpBasicAuth
import dlt
import requests


@dlt.source
def rapid7_source(
    username: str = dlt.secrets.value,
    password: str = dlt.secrets.value,
    host: str = dlt.secrets.value,
    verify: bool = True,
):
    session = requests.Session()
    session.verify = verify
    config: RESTAPIConfig = {
        "client": {
            "base_url": host,
            "auth": HttpBasicAuth(username, password),
            "session": session,
        },
        "resource_defaults": {
            "primary_key": "id",
            "write_disposition": "merge",
            "endpoint": {
                "params": {
                    "size": 500,
                },
            },
        },
        "resources": [
            {
                "name": "assets",
                "endpoint": {
                    "path": "/api/3/assets",
                },
            },
            {
                "name": "vulnerabilities",
                "endpoint": {
                    "path": "/api/3/assets/{resources.assets.id}/vulnerabilities"
                },
            },
        ],
    }

    yield from rest_api_resources(config)

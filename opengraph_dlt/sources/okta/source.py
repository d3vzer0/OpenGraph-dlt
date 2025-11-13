import dlt
from dlt.sources.rest_api.typing import RESTAPIConfig
from dlt.sources.rest_api import rest_api_resources


@dlt.source
def okta_source(access_token=dlt.secrets.value):
    config: RESTAPIConfig = {
        "client": {
            "base_url": "https://okta-domain.okta.com/api/v1/",
            "auth": {
                "type": "bearer",
                "token": access_token,
            },
        },
        "resources": [
            {
                "name": "assets",
                "endpoint": {
                    "path": "users",
                },
            },
            {
                "name": "groups",
                "endpoint": {
                    "path": "groups",
                },
            },
            {
                "name": "roles",
                "endpoint": {
                    "path": "roles",
                },
            },
        ],
    }
    yield from rest_api_resources(config)

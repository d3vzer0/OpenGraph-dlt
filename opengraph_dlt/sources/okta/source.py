import dlt
from dlt.sources.rest_api.typing import RESTAPIConfig
from dlt.sources.rest_api import rest_api_resources


@dlt.source
def okta_source(access_token=dlt.secrets.value):
    config: RESTAPIConfig = {
        "client": {
            "base_url": "https://integrator-5800148.okta.com/api/v1/",
            "auth": {
                "type": "api_key",
                "name": "Authorization",
                "api_key": f"SSWS {access_token}",
            },
        },
        "resources": ["users", "groups", "iam/roles"],
    }
    yield from rest_api_resources(config)

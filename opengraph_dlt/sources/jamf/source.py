import dlt
from dlt.sources.rest_api.typing import RESTAPIConfig
from dlt.sources.rest_api import rest_api_resources


@dlt.source
def jamf_source(
    username=dlt.secrets.value, password=dlt.secrets.value, host=dlt.secrets.value
):
    config: RESTAPIConfig = {
        "client": {
            "base_url": f"{host}/api/v1/",
            "auth": {
                "type": "api_key",
                "name": "Authorization",
                # "api_key": f"SSWS {access_token}",
            },
        },
        "resources": ["users"],
    }
    yield from rest_api_resources(config)

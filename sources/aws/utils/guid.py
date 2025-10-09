from enum import Enum
import uuid
from typing import Optional


class NodeTypes(str, Enum):
    AWSUser = "AWSUser"
    AWSGroup = "AWSGroup"
    AWSRole = "AWSRole"
    AWSIdentityProvider = "AWSIdentityProvider"
    AWSEC2Instance = "AWSEC2Instance"
    AWSPolicy = "AWSPolicy"
    AWSInlinePolicy = "AWSInlinePolicy"


def gen_node_type(node_type: str) -> str:
    pascal_case = "".join(x for x in node_type.title() if not x.isspace())
    return f"AWS{pascal_case}"


def gen_guid(
    name: str,
    node_type: str,
    account_id,
    scope: Optional[str] = "global",
) -> str:
    uuid_namespace = uuid.NAMESPACE_DNS
    resource_path = f"{name}.{node_type}.{account_id}.{scope}"
    return str(uuid.uuid5(uuid_namespace, resource_path))

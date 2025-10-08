from enum import Enum
import uuid
from typing import Optional


class NodeTypes(str, Enum):
    AWSUser = "AWSUser"
    AWSGroup = "AWSGroup"
    AWSRole = "AWSRole"
    AWSIdentityProvider = "AWSIdentityProvider"


def _compose_identity(
    name: str, account_id: Optional[str], scope: Optional[str], node_type: NodeTypes
) -> str:
    segments = [
        "aws",
        account_id or "__unknown__",
        scope or "__global__",
        node_type.value,
        name,
    ]
    return "::".join(segments)


def get_guid(
    name: str,
    node_type: NodeTypes,
    account_id: Optional[str] = None,
    scope: Optional[str] = None,
) -> str:
    identity = _compose_identity(name, account_id, scope, node_type)
    return str(uuid.uuid5(uuid.NAMESPACE_URL, identity))

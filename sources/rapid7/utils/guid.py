from enum import Enum
from typing import Optional
import uuid


class NodeTypes(str, Enum):
    R7Vulnerability = "R7Vulnerability"


def gen_guid(
    name: str, node_type: str, scope: Optional[str] = "global", collector: str = "r7"
) -> str:
    uuid_namespace = uuid.NAMESPACE_DNS
    resource_path = f"{name}.{node_type}.{scope}.{collector}"
    return str(uuid.uuid5(uuid_namespace, resource_path))

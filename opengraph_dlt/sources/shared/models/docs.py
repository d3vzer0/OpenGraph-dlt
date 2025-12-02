from pydantic import BaseModel

RESOURCE_REGISTRY: dict[str, tuple["NodeDef | None", list["EdgeDef"]]] = {}


class NodeDef(BaseModel):
    kind: str
    description: str


class EdgeDef(BaseModel):
    start: str
    end: str
    kind: str
    description: str


def graph_resource(node: NodeDef | None = None, edges: list[EdgeDef] = []):
    def decorator(cls):
        RESOURCE_REGISTRY[cls] = (node, edges)
        return cls

    return decorator

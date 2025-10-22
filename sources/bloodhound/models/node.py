from pydantic import BaseModel


class BloodHoundNode(BaseModel):
    label: str
    kind: str
    kinds: list[str]
    objectId: str
    lastSeen: str

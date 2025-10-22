from pydantic import BaseModel, computed_field
from sources.kubernetes.models.graph import Node, NodeProperties
from sources.kubernetes.utils.guid import get_guid, NodeTypes
from typing import Optional


class GroupVersion(BaseModel):
    group_version: str
    version: str


class ResourceGroup(BaseModel):
    name: str
    api_version: Optional[str] = None

    @computed_field
    @property
    def uid(self) -> str:
        return get_guid(self.name, NodeTypes.KubeResourceGroup, "")


class ResourceGroupNode(Node):

    @property
    def edges(self):
        return []

    @classmethod
    def from_input(cls, **kwargs) -> "ResourceGroupNode":
        model = ResourceGroup(**kwargs)
        properties = NodeProperties(
            name=model.name, displayname=model.name, uid=model.uid, namespace=None
        )
        return cls(kinds=["KubeResourceGroup"], properties=properties)

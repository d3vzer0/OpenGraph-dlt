from pydantic import BaseModel, model_validator, computed_field, Field, field_validator
from ..entries import Node, NodeProperties, Edge, EdgePath
from sources.kubernetes.utils.guid import get_guid, NodeTypes
from typing_extensions import Self
from typing import Optional
import json


class ResourceLookup(BaseModel):
    kind: str
    name: str
    namespace: str | None


class Resource(BaseModel):
    name: str
    categories: Optional[list[str]] = []
    kind: str
    group: Optional[str] = None
    api_version: str = None
    singular_name: str | None = Field(alias="singularName", default=None)
    name: str
    namespaced: bool = False
    verbs: list[str]
    # api_version: str
    # uid: Optional[str] = None
    # api_group_name: Optional[str] = ""
    # api_group_uid: Optional[str] = ""

    @computed_field
    @property
    def uid(self) -> str:
        return get_guid(self.name, NodeTypes.KubeResource, "")

    @field_validator("group", mode="after")
    @classmethod
    def validate_group(cls, v: str) -> str:
        group_name = "__core__" if not v or v == "" else v
        return group_name

    @field_validator("verbs", mode="before")
    @classmethod
    def parse_verbs(cls, value):
        if isinstance(value, str):
            value = json.loads(value)
        return value or []


class ExtendedProperties(NodeProperties):
    kind: str
    api_group_name: Optional[str] = ""
    api_group_uid: Optional[str] = ""


class ResourceNode(Node):
    properties: ExtendedProperties

    @property
    def _resource_group_edge(self):
        if self.properties.api_group_name:
            target_id = get_guid(
                self.properties.api_group_name,
                NodeTypes.KubeResourceGroup,
                self._cluster,
            )
            start_path = EdgePath(value=self.id, match_by="id")
            end_path = EdgePath(value=target_id, match_by="id")
            edge = Edge(kind="KubeInResourceGroup", start=start_path, end=end_path)
            return edge
        else:
            return None

    @property
    def edges(self):
        resource_group_edge = (
            [self._resource_group_edge] if self._resource_group_edge else []
        )
        return resource_group_edge

    @classmethod
    def from_input(cls, **kwargs) -> "ResourceNode":
        model = Resource(**kwargs)
        properties = ExtendedProperties(
            name=model.name,
            displayname=model.name,
            kind=model.kind,
            namespace=None,
            api_group_name=model.group,
            uid=model.uid,
        )
        return cls(kinds=["KubeResource"], properties=properties)


# class CustomResourceNode(Node):
#     properties: ExtendedProperties

#     @property
#     def _resource_group_edge(self):
#         if self.properties.api_group_name:
#             target_id = get_guid(
#                 self.properties.api_group_name,
#                 NodeTypes.KubeResourceGroup,
#                 self._cluster,
#             )
#             start_path = EdgePath(value=self.id, match_by="id")
#             end_path = EdgePath(value=target_id, match_by="id")
#             edge = Edge(kind="KubeInResourceGroup", start=start_path, end=end_path)
#             return edge
#         else:
#             return None

#     @property
#     def edges(self):
#         resource_group_edge = (
#             [self._resource_group_edge] if self._resource_group_edge else []
#         )
#         return resource_group_edge

#     @classmethod
#     def from_input(cls, **kwargs) -> "CustomResourceNode":
#         model = Resource(**kwargs)
#         properties = ExtendedProperties(
#             name=model.name,
#             displayname=model.name,
#             namespace=None,
#             kind=model.kind,
#             api_group_name=model.api_group_name,
#             api_group_uid=model.api_group_uid,
#             uid=model.uid,
#         )
#         return cls(kinds=["KubeResource"], properties=properties)

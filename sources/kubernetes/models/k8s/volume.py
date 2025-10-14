from pydantic import BaseModel, computed_field, ConfigDict
from sources.kubernetes.utils.guid import get_guid, NodeTypes
from ..entries import Node, NodeProperties, Edge, EdgePath


class Volume(BaseModel):
    node_name: str
    path: str
    # cluster: str

    @computed_field
    @property
    def name(self) -> str:
        return f"fs://{self.node_name}{self.path}"

    @computed_field
    @property
    def uid(self) -> str:
        return get_guid(self.name, NodeTypes.KubeVolume, "")


class ExtendedProperties(NodeProperties):
    model_config = ConfigDict(extra="allow")
    node_name: str


class VolumeNode(Node):
    properties: ExtendedProperties

    @property
    def _node_edge(self):
        start_path = EdgePath(value=self.id, match_by="id")
        end_path_id = get_guid(
            self.properties.node_name, NodeTypes.KubeNode, self._cluster
        )
        end_path = EdgePath(value=end_path_id, match_by="id")
        edge = Edge(kind="KubeHostedOn", start=start_path, end=end_path)
        return edge

    @property
    def edges(self):
        return [self._node_edge]

    @classmethod
    def from_input(cls, **kwargs) -> "VolumeNode":
        model = Volume(**kwargs)
        properties = ExtendedProperties(
            name=model.name,
            displayname=model.name,
            node_name=model.node_name,
            namespace=None,
            uid=model.uid,
        )
        node = cls(kinds=["KubeVolume"], properties=properties)
        return node

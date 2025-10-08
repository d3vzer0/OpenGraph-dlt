from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


from sources.aws.utils.guid import NodeTypes
from ..entries import Node, NodeProperties
from .role import Role


class EC2InstanceRole(Role):
    InstanceId: str
    InstanceRegion: Optional[str] = None
    InstanceArn: Optional[str] = None


class EC2Instance(BaseModel):
    model_config = ConfigDict(extra="allow")
    InstanceId: str
    InstanceType: str
    Arn: Optional[str] = None
    LaunchTime: Optional[datetime] = None
    # State: Optional[dict] = None
    # IamInstanceProfile: Optional[dict] = None
    PrivateIpAddress: Optional[str] = None
    PublicIpAddress: Optional[str] = None
    AccountId: Optional[str] = None
    Region: Optional[str] = None


class EC2InstanceProperties(NodeProperties):
    model_config = ConfigDict(extra="allow")
    instance_type: str
    state: Optional[str] = None
    private_ip: Optional[str] = None
    public_ip: Optional[str] = None
    instance_profile_arn: Optional[str] = None
    region: Optional[str] = None
    launch_time: Optional[datetime] = None


class EC2InstanceNode(Node):
    properties: EC2InstanceProperties

    @property
    def edges(self):
        return []

    # @classmethod
    # def from_input(cls, **kwargs) -> "EC2InstanceNode":

    #     node = cls(kinds=[NodeTypes.AWSEC2Instance.value], properties=properties)
    #     node.attach_context(model.AccountId, scope=model.Region)
    #     return node

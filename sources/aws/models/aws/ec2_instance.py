from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


from sources.aws.utils.guid import NodeTypes
from ..entries import Node, NodeProperties
from .role import Role


class EC2InstanceRole(Role):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    instance_id: str = Field(alias="InstanceId")
    instance_region: Optional[str] = Field(alias="InstanceRegion", default=None)
    instance_arn: Optional[str] = Field(alias="InstanceArn", default=None)


class EC2Instance(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)
    instance_id: str = Field(alias="InstanceId")
    instance_type: str = Field(alias="InstanceType")
    arn: Optional[str] = Field(alias="Arn", default=None)
    launch_time: Optional[datetime] = Field(alias="LaunchTime", default=None)
    private_ip_address: Optional[str] = Field(alias="PrivateIpAddress", default=None)
    public_ip_address: Optional[str] = Field(alias="PublicIpAddress", default=None)
    account_id: Optional[str] = Field(alias="AccountId", default=None)
    region: Optional[str] = Field(alias="Region", default=None)


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

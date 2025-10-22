from pydantic import BaseModel, Field
from typing import Optional


class VulnerabilityCount(BaseModel):
    critical: int
    exploits: int
    malwareKits: int
    moderate: int
    severe: int
    total: int


class Service(BaseModel):
    name: str
    port: int
    protocol: str


class Address(BaseModel):
    ip: str
    mac: str


class HostName(BaseModel):
    name: str
    source: str


class Asset(BaseModel):
    id: int
    os: str
    ip: str
    host_name: Optional[str] = Field(alias="hostName", default=None)
    host_names: Optional[list[HostName]] = Field(alias="hostNames", default=None)
    mac: str
    raw_risk_score: float = Field(alias="rawRiskScore")
    risk_score: float = Field(alias="riskScore")
    addresses: list[Address]
    services: list[Service]
    assessed_for_vulnerabilities: bool = Field(alias="assessedForVulnerabilities")
    assessed_for_policies: bool = Field(alias="assessedForPolicies")
    vulnerabilities: VulnerabilityCount

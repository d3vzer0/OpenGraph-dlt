from pydantic import BaseModel


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


class Asset(BaseModel):
    id: int
    os: str
    ip: str
    mac: str
    rawRiskScore: float
    riskScore: float
    addresses: list[Address]
    services: list[Service]
    assessedForVulnerabilities: bool
    assessedForPolicies: bool

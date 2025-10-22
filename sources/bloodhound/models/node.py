from pydantic import BaseModel


class Properties(BaseModel):
    caname: str | None = None
    certname: str | None = None
    description: str | None = None
    displayname: str | None = None
    name: str | None = None
    distinguishedname: str | None = None
    dnshostname: str | None = None
    domain: str | None = None
    domainsid: str | None = None
    email: str | None = None
    operatingsystem: str | None = None
    title: str | None = None


class BloodHoundNode(BaseModel):
    label: str
    kind: str
    kinds: list[str]
    objectId: str
    lastSeen: str
    properties: Properties

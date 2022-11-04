from pydantic import BaseModel


class Database(BaseModel):
    database: str
    host: str
    user: str
    password: str


class InstanceBaseConfig(BaseModel):
    tenant_id: str
    version: str


class InstanceSetupConfig(InstanceBaseConfig):
    slug: str
    name: str
    db: Database


class InstanceCreationRequest(BaseModel):
    tenant_id: str
    slug: str
    name: str
    version: str


class InstanceUpdateRequest(BaseModel):
    tenant_id: str
    version: str

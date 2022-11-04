from pydantic import BaseModel


class Database(BaseModel):
    database: str
    host: str
    user: str
    password: str


class InstanceConfig(BaseModel):
    tenant_id: str
    slug: str
    name: str
    db: Database


class InstanceCreationRequest(BaseModel):
    tenant_id: str
    slug: str
    name: str

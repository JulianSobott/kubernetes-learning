from pydantic import BaseModel


class InstanceConfig(BaseModel):
    tenant_id: str
    slug: str
    name: str

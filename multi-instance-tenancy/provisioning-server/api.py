import os
import uuid

from fastapi import APIRouter, Response

import db
from k8s import deploy_instance, delete_instance, first_deployment
from models import InstanceCreationRequest, Database, InstanceSetupConfig, \
    InstanceBaseConfig, InstanceUpdateRequest

router = APIRouter()

db_host_k8s = os.environ.get("DB_HOST")


@router.post("/instance")
async def create_instance(req: InstanceCreationRequest):
    db_config = Database(
        database=_db_database_name(req.tenant_id),
        host=db_host_k8s,
        user=_db_user_name(req.tenant_id),
        password=uuid.uuid4().hex,
    )
    instance = InstanceSetupConfig(
        tenant_id=req.tenant_id,
        slug=req.slug,
        name=req.name,
        db=db_config,
        version=req.version,
    )
    err = db.create_database(instance)
    if err:
        return {"message": f"Error creating database: {err}"}
    first_deployment(instance)
    instance_url = deploy_instance(instance)
    return Response(status_code=302, headers={"Location": instance_url})


@router.put("/instance/{tenant_id}")
async def update_instance(tenant_id: str, req: InstanceUpdateRequest):
    assert tenant_id == req.tenant_id
    instance = InstanceBaseConfig(
        tenant_id=req.tenant_id,
        version=req.version,
    )
    instance_url = deploy_instance(instance)
    return Response(status_code=302, headers={"Location": instance_url})


@router.delete("/instance/{tenant_id}")
async def api_delete_instance(tenant_id: str):
    delete_instance(tenant_id)
    db.delete_database(_db_database_name(tenant_id), _db_user_name(tenant_id))
    return Response(status_code=204)


def _db_database_name(tenant_id: str):
    return f"example_app_{tenant_id}"


def _db_user_name(tenant_id: str):
    return f"tenant_{tenant_id}"

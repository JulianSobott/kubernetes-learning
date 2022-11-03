from fastapi import APIRouter, Request, Response

from k8s import deploy_instance
from models import InstanceConfig

router = APIRouter()


@router.post("/instance")
async def create_instance(config: InstanceConfig):
    instance_url = deploy_instance(config)
    return Response(status_code=302, headers={"Location": instance_url})

import uuid
import logging
import os

from fastapi import FastAPI

app = FastAPI()
logger = logging.getLogger(__name__)


tenant = os.environ.get("TENANT", "default")

@app.get("/")
async def root():
    return {"message": f"Hello {tenant}!"}

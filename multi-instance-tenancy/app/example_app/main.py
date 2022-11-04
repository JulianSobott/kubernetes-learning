import uuid
import logging
import os

from fastapi import FastAPI
from mysql.connector import connect, Error

app = FastAPI()
logger = logging.getLogger(__name__)


tenant = os.environ.get("TENANT", "default")
db_user = os.environ.get("DB_USER", "default")
db_password = os.environ.get("DB_PASSWORD", "default")
db_host = os.environ.get("DB_HOST", "default")
db_database = os.environ.get("DB_DATABASE", "default")


@app.get("/")
async def root():
    with connect(
        host=db_host,
        user=db_user,
        password=db_password,
        database=db_database,
    ) as connection:
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                logger.info(f"Result: {result}")
        except Error as e:
            logger.error(e)
            return {"message": f"Hello {tenant}! {e}"}
    return {"message": f"Hello {tenant}!", "result": result}

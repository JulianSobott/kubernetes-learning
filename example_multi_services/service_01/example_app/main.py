import uuid
import logging

from fastapi import FastAPI

app = FastAPI()
app_name = uuid.uuid4()


logger = logging.getLogger(__name__)
i = 0


@app.get("/")
async def root():
    global i
    i += 1
    return {"message": "Hello World!", "app_name": app_name, "number_of_calls": i}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}

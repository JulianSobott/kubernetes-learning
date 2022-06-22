import uuid

from fastapi import FastAPI

app = FastAPI()
app_name = uuid.uuid4()


@app.get("/")
async def root():
    return {"message": "Hello World", "app_name": app_name}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}

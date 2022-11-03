from fastapi import FastAPI

from api import router as api_router

app = FastAPI()
app.include_router(api_router, prefix="/api")


@app.get("/")
async def root():
    return {"message": "Hello World"}

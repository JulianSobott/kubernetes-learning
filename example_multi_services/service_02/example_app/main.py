import requests

from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def root():
    response = requests.get("http://service-01:8080")
    try:
        body = response.json()
    except:
        body = response.text
    return {"status": response.status_code, "body": body}

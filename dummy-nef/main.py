from typing import Union
from fastapi import FastAPI
import httpx

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/test")
async def test_conn():

    async with httpx.AsyncClient(http1=False, http2=True) as client:
        response = await client.get(
            "http://10.244.2.53:80/nnrf-nfm/v1/nf-instances",
            headers={'Accept': 'application/json'}
        )
        print(response.http_version)
        print(response.text)
    return response.json()
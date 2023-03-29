from typing import Union
from fastapi import FastAPI
import httpx

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/test2")
async def test_conn2():
    async with httpx.AsyncClient(http2=True, verify=False) as client:
        response = await client.get(
            "http://10.244.2.52/nnrf-nfm/v1/nf-instances",
            headers={'Accept': 'application/json,application/problem+json'},
        )
        print(response.text)
    return response.json()

@app.get("/test")
async def test_conn():
    async with httpx.AsyncClient(http2=True, verify=False, alpn_protocols=["h2"], ssl="TLSv1.2") as client:
        response = await client.get(
            "https://10.244.2.42/nnrf-nfm/v1/nf-instances",
            headers={'Accept': 'application/json,application/problem+json'}
        )
        print(response.text)
    return response.json()
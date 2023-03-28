from typing import Union
from fastapi import FastAPI
import httpx
from open5gs import create_ssl_context_for_client

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/test2")
async def test_conn2():
    ssl_ctx = create_ssl_context_for_client()

    async with httpx.AsyncClient(http2=True, verify=False, ssl=ssl_ctx) as client:
        response = await client.get(
            "https://10.244.2.42/nnrf-nfm/v1/nf-instances",
            headers={'Accept': 'application/json'},
        )
        print(response.text)
    return response.json()

@app.get("/test")
async def test_conn():
    async with httpx.AsyncClient(http2=True, verify=False, alpn_protocols=["h2"], ssl="TLSv1.3") as client:
        response = await client.get("https://10.244.2.42:80//nnrf-nfm/v1/nf-instances", headers={'Accept': 'application/json'})
        print(response.text)
    return response.json()
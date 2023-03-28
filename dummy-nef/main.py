from typing import Union
from fastapi import FastAPI
import ssl
import httpx
from httpx._config import SSLConfig

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/test2")
async def test_conn2():
    ctx = SSLConfig().with_ssl_context(
        ssl.create_default_context()
    )
    ctx.ssl_version = ssl.PROTOCOL_TLSv1_2
    ctx.ciphers = "ECDHE-RSA-AES128-GCM-SHA256"
    ctx.alpn_protocols = ["h2"]

    async with httpx.AsyncClient(http2=True, verify=False, ssl=ctx) as client:
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
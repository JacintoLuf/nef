from typing import Union
from fastapi import FastAPI
import httpx
from httx._config import SSLConfig
import ssl

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/test2")
async def test_conn2():
    ssl = SSLConfig(
        version=ssl.PROTOCOL_TLSv1_2,
        cipher_suite=ssl.TLS_CIPHERS_ECDHE_RSA_WITH_AES_128_GCM_SHA256,
        alpn_protocols=["h2"]
    )

    async with httpx.AsyncClient(http2=True, verify=False, ssl=ssl) as client:
        response = await client.get(
            "https://10.244.2.52/nnrf-nfm/v1/nf-instances",
            headers={'Accept': 'application/json,application/problem+json'},
        )
        print(response.text)
    return response.json()

@app.get("/test")
async def test_conn():
    ctx = SSLConfig().with_ssl_context(
        ssl.create_default_context()
    )
    ctx.ssl_version = ssl.PROTOCOL_TLSv1_2
    ctx.ciphers = "ECDHE-RSA-AES128-GCM-SHA256"
    ctx.alpn_protocols = ["h2"]

    async with httpx.AsyncClient(http2=True, verify=False, ssl=ctx) as client:
        response = await client.get(
            "https://10.244.2.42/nnrf-nfm/v1/nf-instances",
            headers={'Accept': 'application/json,application/problem+json'}
        )
        print(response.text)
    return response.json()
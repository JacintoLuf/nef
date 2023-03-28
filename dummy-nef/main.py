from typing import Union
from fastapi import FastAPI
#from hyper import HTTPConnection
import httpx
from httpx._config import SSLConfig

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/test2")
async def test_conn2():
    ssl = SSLConfig(
        version=ssl.PROTOCOL_TLSv1_2,
        cipher_suite=ssl.TLS_CIPHERS_ECDHE_RSA_WITH_AES_128_GCM_SHA256,
    )

    async with httpx.AsyncClient(http2=True, verify=False, ssl=ssl) as client:
        response = await client.get("https://10.244.2.42:80//nnrf-nfm/v1/nf-instances", headers={'Accept': 'application/json'})
        print(response.text)
    return response.json()

@app.get("/test")
async def test_conn():
    async with httpx.AsyncClient(http2=True, verify=False, alpn_protocols=["h2"], ssl="TLSv1.3") as client:
        response = await client.get("https://10.244.2.42:80//nnrf-nfm/v1/nf-instances", headers={'Accept': 'application/json'})
        print(response.text)
    return response.json()
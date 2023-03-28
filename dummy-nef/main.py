from typing import Union
from fastapi import FastAPI
#from hyper import HTTPConnection
import httpx

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/test2")
async def test_conn2():
    async with httpx.AsyncClient(http2=True, verify=False) as client:
        response = await client.get("https://10.244.2.42:80//nnrf-nfm/v1/nf-instances", headers={'Accept': 'application/json'})
    return response.json()

@app.get("/test")
def test_conn():
    endpoint = "https://10.244.2.42:80"

    conn = HTTPConnection(endpoint)
    conn.request('GET', '/nnrf-nfm/v1/nf-instances', headers={'Accept': 'application/json'})
    response = conn.get_response()

    print(response.status_code)
    print(response.content)

    return {"mesage": response.read()}
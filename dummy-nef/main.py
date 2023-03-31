from typing import Union
from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from models.nf_profile import NFProfile
#from pydantic import BaseModel
import httpx
import logging

app = FastAPI()
logger = logging.getLogger(__name__)
nef_profile = NFProfile()
tmp = {}


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
        logger.debug("resonse code: %s", response.status_code)
        print(response.status_code)
        print(response.headers)
        print(response.text)
    return response.text

@app.get("/test2")
async def test_conn():

    async with httpx.AsyncClient(http1=False, http2=True) as client:
        response = await client.get(
            "http://10.106.127.186:80/nnrf-disc/v1/nf-instances",
            headers={'Accept': 'application/json,application/problem+json'},
            params= {"target-nf-type": "AMF", "requester-nf-type": "NEF"}
        )
        logger.debug("resonse code: %s", response.status_code)
        print(response.status_code)
        print(response.headers)
        print(response.text)
    return response.text

@app.get("/nf-register")
async def register_nf():
    async with httpx.AsyncClient(http1=False, http2=True) as client:
        response = await client.put(
            "http://10.106.127.186:80/nnrf-nfm/v1/nf-instances/"+nef_profile.nf_instance_id,
            headers={'Accept': 'application/json,application/problem+json'}
        )
        print(response.text)
    return response.text

@app.get("/nf-discovery/{nfType}")
async def get_nf_instances():
    async with httpx.AsyncClient(http1=False, http2=True) as client:
        response = await client.get(
            "http://10.244.2.53:80/nnrf-nfm/v1/",
            headers={'Accept': 'application/json,application/problem+json'}
        )
        print(response.text)
    return response.text
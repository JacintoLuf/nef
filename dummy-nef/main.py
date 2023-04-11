from fastapi import FastAPI
from models.nf_profile import NFProfile
from session import static_client, close
from init_db import init_db
import httpx
import logging
import json
import logging

app = FastAPI()
logger = logging.getLogger(__name__)
nef_profile = NFProfile()
tmp = {}
nrf = "10.106.127.186:80"
amf = "10.111.27.77:80"
smf = "10.111.153.168:80"


@app.on_event("startup")
async def startup():
    try:
        db = static_client
        init_db(db)
        uuids = []
        instances = {}
        async with httpx.AsyncClient(http1=False, http2=True) as client:
            response = await client.get(
                "http://"+nrf+"/nnrf-nfm/v1/nf-instances",
                headers={'Accept': 'application/json'}
            )
            logger.debug("resonse code: %s", response.status_code)
            j = json.loads(response.text)
            uuids = [i["href"].split('/')[-1] for i in j["_links"]["items"]]
        async with httpx.AsyncClient(http1=False, http2=True) as client:
            for x in len(uuids):
                response = await client.get(
                    "http://"+nrf+"/nnrf-nfm/v1/nf-instances/"+uuids[x],
                    headers={'Accept': 'application/json'}
                )
                instances[x] = response.text
        print(instances)
    except Exception as e:
        logger.error(e)
        print(e)
        raise e
    
@app.on_event("shutdown")
async def shutdown():
    print("Database reset complete.")
    close()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/test")
async def test_conn():

    async with httpx.AsyncClient(http1=False, http2=True) as client:
        response = await client.get(
            "http://"+nrf+"/nnrf-nfm/v1/nf-instances",
            headers={'Accept': 'application/json'}
        )
        logger.debug("resonse code: %s", response.status_code)
        print(response.text)
        j = json.loads(response.text)
        links = [i["href"].split('/')[-1] for i in j["_links"]["items"]]
        print(links)
    return response.text

@app.get("/test2")
async def test_conn():

    async with httpx.AsyncClient(http1=False, http2=True) as client:
        response = await client.get(
            "http://"+nrf+"/nnrf-disc/v1/nf-instances",
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
            "http://"+nrf+"/nnrf-nfm/v1/nf-instances/"+nef_profile.nf_instance_id,
            headers={'Accept': 'application/json,application/problem+json'}
        )
        print(response.text)
    return response.text

@app.get("/test3")
async def get_nf_instances():
    async with httpx.AsyncClient(http1=False, http2=True) as client:
        response = await client.get(
            "http://"+nrf+"/nnrf-nfm/v1/",
            headers={'Accept': 'application/json,application/problem+json'}
        )
        print(response.text)
    return response.text

@app.get("/smf-test")
async def test_smf():
    """smf event exposure"""
    return ""

@app.get("/smf-test2")
async def test_smf():
    """smf NIDD"""
    return ""
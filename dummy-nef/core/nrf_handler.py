import httpx
import json
import uuid
from api.config import conf
from session import db
from models import nf_profile
from crud import nf_profiles


async def nrf_discovery():
    collection = db["nf_instances"]
    uuids = []
    instances = []

    x = collection.delete_many({})
    print(x.deleted_count, " documents deleted.")

    print("---------------------------------------")
    print("discover NF profiles")
    async with httpx.AsyncClient(http1=False, http2=True) as client:
        response = await client.get(
            "http://"+conf.NRF_IP+"/nnrf-disc/v1/nf-instances",
            headers={'Accept': 'application/json,application/problem+json'},
            params = {'requester-nf-type': 'NEF'} #'target-nf-type': 'NSSF',  
        )
        print(response.txt)
    
    print("---------------------------------------")
    async with httpx.AsyncClient(http1=False, http2=True) as client:
        response = await client.get(
            "http://"+conf.NRF_IP+"/nnrf-nfm/v1/nf-instances",
            headers={'Accept': 'application/json,application/problem+json'},
        )
        j = json.loads(response.text)
        uuids = [i["href"].split('/')[-1] for i in j["_links"]["items"]]

    async with httpx.AsyncClient(http1=False, http2=True) as client:
        for id in uuids:
            response = await client.get(
                "http://"+conf.NRF_IP+"/nnrf-nfm/v1/nf-instances/"+id,
                headers={'Accept': 'application/json,application/problem+json'}
            )
            instances.append(json.loads(response.text))
            #result = collection.insert_one(json.loads(response.text))
    result = collection.insert_many(instances)
    result.inserted_ids
    print("after")
    for inst in collection.find():
        print(inst)
    return None

async def nf_register():
    async with httpx.AsyncClient(http1=False, http2=True) as client:
        response = await client.options(
            "http://"+conf.NRF_IP+"/nnrf-nfm/v1/nf-instances",
        )
        print(f"NRF nf-instances OPTIONS: {response.text}")


    return None

def nf_deregister():

    return None
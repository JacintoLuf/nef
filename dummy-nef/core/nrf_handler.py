import httpx
import json
import uuid
from api.config import conf
from session import db
from models.nf_profile import NFProfile
from crud import nfProfile


async def nrf_discovery():
    collection = db["nf_instances"]
    uuids = []
    instances = []
    profiles = []

    async with httpx.AsyncClient(http1=False, http2=True) as client:
        response = await client.get(
            "http://"+conf.NF_IP["NRF"][0]+":7777/nnrf-nfm/v1/nf-instances",
            headers={'Accept': 'application/json,application/problem+json'},
        )
        j = json.loads(response.text)
        uuids = [i["href"].split('/')[-1] for i in j["_links"]["items"]]

    async with httpx.AsyncClient(http1=False, http2=True) as client:
        for id in uuids:
            response = await client.get(
                "http://"+conf.NF_IP["NRF"][0]+":7777/nnrf-nfm/v1/nf-instances/"+id,
                headers={'Accept': 'application/json,application/problem+json'}
            )
            profiles.append(NFProfile.from_dict(response.json()))
            instances.append(response.json())
    #await nfProfile.insert_many(instances)
    conf.set_nf_endpoints(profiles)
    result = collection.insert_many(instances)
    result.inserted_ids
    #print(collection.count_documents())
    return None

async def nf_register():
    async with httpx.AsyncClient(http1=False, http2=True) as client:
        response = await client.options(
            "http://"+conf.NF_IP["NRF"]+"7777/nnrf-nfm/v1/nf-instances",
        )
        print(f"NRF nf-instances OPTIONS: {response.text}")

    async with httpx.AsyncClient(http1=False, http2=True) as client:
        response = await client.put(
            "http://"+conf.NF_IP["NRF"]+"7777/nnrf-nfm/v1/nf-instances/"+conf.NEF_PROFILE.nf_instance_id,
            headers={'Accept': 'application/json,application/problem+json'}
        )
        print(response.text)

    return None

def nf_deregister():

    return None
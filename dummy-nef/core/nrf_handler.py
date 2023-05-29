import httpx
import json
import uuid
from api.config import conf
from session import db
from models.nf_profile import NFProfile
from crud import nfProfile


async def nrf_discovery() -> str:
    collection = db["nf_instances"]
    uuids = []
    instances = []
    profiles = []

    collection.delete_many({})

    async with httpx.AsyncClient(http1=False, http2=True) as client:
        response = await client.get(
            "http://"+conf.HOSTS["NRF"][0]+":7777/nnrf-nfm/v1/nf-instances",
            headers={'Accept': 'application/json,application/problem+json'},
        )
        j = json.loads(response.text)
        uuids = [i["href"].split('/')[-1] for i in j["_links"]["items"]]

    async with httpx.AsyncClient(http1=False, http2=True) as client:
        for id in uuids:
            response = await client.get(
                "http://"+conf.HOSTS["NRF"][0]+":7777/nnrf-nfm/v1/nf-instances/"+id,
                headers={'Accept': 'application/json,application/problem+json'}
            )
            profiles.append(NFProfile.from_dict(response.json()))
            instances.append(response.json())
    #await nfProfile.insert_many(instances)
    conf.set_nf_endpoints(profiles)
    result = collection.insert_many(instances)
    result.inserted_ids
    print(instances[0])
    #print(collection.count_documents())
    return "NF profiles loaded"

async def nf_register() -> str:
    print(json.dumps(conf.NEF_PROFILE.to_dict()))
    nef_profile = conf.NEF_PROFILE.to_dict()
    nef_profile.pop('nfServicePersistence')
    nef_profile.pop('nfProfileChangesSupportInd')
    nef_profile.pop('nfProfileChangesInd')
    nef_profile.pop('lcHSupportInd')
    nef_profile.pop('olcHSupportInd')
    print(nef_profile)

    async with httpx.AsyncClient(http1=False, http2=True) as client:
        response = await client.put(
            "http://"+conf.HOSTS["NRF"][0]+":7777/nnrf-nfm/v1/nf-instances/"+conf.NEF_PROFILE.nf_instance_id,
            headers={
                'Accept': 'application/json,application/problem+json',
                'Content-Encoding': 'string',
                'Content-Type': 'application/json'
                },
            data = nef_profile
        )
        print(response.text)

    return response.text

def nf_deregister():

    return None
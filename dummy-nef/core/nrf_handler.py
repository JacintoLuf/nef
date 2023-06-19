import httpx
import json
from api.config import conf
from session import db
from models.nf_profile import NFProfile
from crud import nfProfile

async def nrf_discovery() -> int:
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
    # result = collection.insert_many(instances)
    # #result = collection.update_many(instances)
    # result.inserted_ids
    # print("Core NF instances saved")

    collection.update_many([{'nfInstanceId': i['nfInstanceId']} for i in instances], instances, upsert=True)
    print("Core NF instances saved")

    
    return 1

async def nf_register() -> int:

    async with httpx.AsyncClient(http1=False, http2=True) as client:
        response = await client.put(
            "http://"+conf.HOSTS["NRF"][0]+":7777/nnrf-nfm/v1/nf-instances/"+conf.NEF_PROFILE.nf_instance_id,
            headers={
                'Accept': 'application/json,application/problem+json',
                'Content-Type': 'application/json'
                },
            data = json.dumps(conf.NEF_PROFILE.to_dict())
        )
        if response.status_code == httpx.codes.CREATED:
            print(f"[{conf.NEF_PROFILE.nf_instance_id}] NF registerd [Heartbeat: {conf.NEF_PROFILE.heart_beat_timer}]")
        else:
            print(response.text)

    return response.status_code

async def nf_upfate() -> int:

    return 1

async def nf_deregister() -> int:
    async with httpx.AsyncClient(http1=False, http2=True) as client:
        response = await client.delete(
            "http://"+conf.HOSTS["NRF"][0]+":7777/nnrf-nfm/v1/nf-instances/"+conf.NEF_PROFILE.nf_instance_id,
            headers={'Accept': 'application/json,application/problem+json'}
        )
        print(response.status_code)
        print(response.text)
        if response.status_code == httpx.codes.NO_CONTENT:
            print(f"[{conf.NEF_PROFILE.nf_instance_id}] NF de-registered")
        if response.status_code == httpx.codes.NOT_FOUND:
            print("NEF instance not registered")

    return response.status_code

async def nf_register_heart_beat() -> int:
    async with httpx.AsyncClient(http1=False, http2=True) as client:
        response = await client.patch(
            "http://"+conf.HOSTS["NRF"][0]+":7777/nnrf-nfm/v1/nf-instances/"+conf.NEF_PROFILE.nf_instance_id,
            headers={
                'Accept': 'application/json,application/problem+json',
                'Content-Type': 'application/json-patch+json'
                },
            data = json.dumps([{ "op": "replace", "path": "/nfStatus", "value": "REGISTERED" }])
        )
        if response.status_code == httpx.codes.OK:
            new_nef_profile = NFProfile.from_dict(response.json())
            print(f"new profile {json.dumps(new_nef_profile)}")
        # elif response.status_code == httpx.codes.NO_CONTENT:
        #     print("NRF Heart-Beat!")
        elif response.status_code == httpx.codes.NOT_FOUND:
            print("NEF instance not registered")

    return response.status_code

async def nf_status_subscribe() -> int:

    return 1

async def nf_status_notify() -> int:

    return 1

async def nf_status_unsubscribe() -> int:

    return 1
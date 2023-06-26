import httpx
import json
from api.config import conf
from session import db
from models.nf_profile import NFProfile
#from models.subscription_data import SubscriptionData
import crud.nfProfile as nfProfile

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
            # res = nfProfile.insert_one(response.json())
            # print(res)
            instances.append(response.json())
    conf.set_nf_endpoints(profiles)
    res = nfProfile.insert_many(instances)
    #result = collection.insert_many(instances)
    print("Core NF instances saved")

    return 1

async def nf_register():

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

async def nf_update(profile):

    return 1

async def nf_deregister():
    async with httpx.AsyncClient(http1=False, http2=True) as client:
        response = await client.delete(
            "http://"+conf.HOSTS["NRF"][0]+":7777/nnrf-nfm/v1/nf-instances/"+conf.NEF_PROFILE.nf_instance_id,
            headers={'Accept': 'application/json,application/problem+json'}
        )
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

async def nf_status_subscribe():
    async with httpx.AsyncClient(http1=False, http2=True) as client:
        response = await client.post(
            f"http://{conf.HOSTS['NRF'][0]}:7777/nnrf-nfm/v1/subscriptions",
            headers={
                'Accept': 'application/json,application/problem+json',
                'Content-Type': 'application/json-patch+json'
                },
            data = ""
        )
        print(response.text)
    return 1

async def nf_status_unsubscribe(subId):
    async with httpx.AsyncClient(http1=False, http2=True) as client:
            response = await client.patch(
                f"http://{conf.HOSTS['NRF'][0]}:7777/nnrf-nfm/v1/subscriptions/{subId}",
                headers={
                    'Accept': 'application/json,application/problem+json',
                    'Content-Type': 'application/json-patch+json'
                    }
            )
            print(response.text)
    return 1
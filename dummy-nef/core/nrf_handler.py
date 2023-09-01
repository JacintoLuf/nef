import httpx
import json
from api.config import conf
from session import async_db
from models.nf_profile import NFProfile
from models.subscription_data import SubscriptionData
from models.subscr_cond import SubscrCond
from models.access_token_req import AccessTokenReq
import crud.nfProfile as nfProfile
import crud.subscriptionData as subscriptionData

async def nrf_discovery():
    uuids = []
    instances = []
    profiles = []
    collection = async_db['nf_instances']
    collection.delete_many({})
    async with httpx.AsyncClient(http1=False, http2=True) as client:
        response = await client.get(
            f"http://{conf.HOSTS['NRF'][0]}:7777/nnrf-nfm/v1/nf-instances",
            headers={'Accept': 'application/json,application/problem+json'},
        )
        j = json.loads(response.text)
        uuids = [i["href"].split('/')[-1] for i in j["_links"]["items"]]

    async with httpx.AsyncClient(http1=False, http2=True) as client:
        for id in uuids:
            response = await client.get(
                f"http://{conf.HOSTS['NRF'][0]}:7777/nnrf-nfm/v1/nf-instances/"+id,
                headers={'Accept': 'application/json,application/problem+json'}
            )
            profiles.append(NFProfile.from_dict(response.json()))
            res = await nfProfile.insert_one(response.json())
            instances.append(response.json())
    conf.set_nf_endpoints(profiles)
    return 1

async def nrf_get_access_token():
    for key in conf.NF_SCOPES.keys():
        access_token_req = AccessTokenReq(
            grant_type="client_credentials",
            nf_instance_id=conf.API_UUID,
            nf_type="NEF",
            target_nf_type=key,
            scope=conf.NF_SCOPES[key],
        )
        async with httpx.AsyncClient(http1=False, http2=True) as client:
            response = await client.post(
                f"http://{conf.HOSTS['NRF'][0]}:7777/nnrf-nfm/v1/nf-instances",
                headers={'Accept': 'application/json,application/problem+json'},
                data=json.dumps(access_token_req.to_dict())
            )
            print(response.status_code)
            print(response.text)
    return 200

async def nf_register():
    async with httpx.AsyncClient(http1=False, http2=True) as client:
        response = await client.put(
            f"http://{conf.HOSTS['NRF'][0]}:7777/nnrf-nfm/v1/nf-instances/"+conf.NEF_PROFILE.nf_instance_id,
            headers={
                'Accept': 'application/json,application/problem+json',
                'Content-Type': 'application/json'
                },
            data = json.dumps(conf.NEF_PROFILE.to_dict())
        )
        if response.status_code == httpx.codes.CREATED:
            print(f"[{conf.NEF_PROFILE.nf_instance_id}] NF registerd [Heartbeat:{conf.NEF_PROFILE.heart_beat_timer}s]")
        else:
            print(response.text)
    return response

async def nf_update(profile):

    return 1

async def nf_deregister():
    async with httpx.AsyncClient(http1=False, http2=True) as client:
        response = await client.delete(
            f"http://{conf.HOSTS['NRF'][0]}:7777/nnrf-nfm/v1/nf-instances/"+conf.NEF_PROFILE.nf_instance_id,
            headers={'Accept': 'application/json,application/problem+json'}
        )
        print(response.text)
        if response.status_code == httpx.codes.NO_CONTENT:
            print(f"[{conf.NEF_PROFILE.nf_instance_id}] NF de-registered")
        if response.status_code == httpx.codes.NOT_FOUND:
            print("NEF instance not registered")

    return response.status_code

async def nf_register_heart_beat():
    async with httpx.AsyncClient(http1=False, http2=True) as client:
        response = await client.patch(
            f"http://{conf.HOSTS['NRF'][0]}:7777/nnrf-nfm/v1/nf-instances/"+conf.NEF_PROFILE.nf_instance_id,
            headers={
                'Accept': 'application/json,application/problem+json',
                'Content-Type': 'application/json-patch+json'
                },
            data = json.dumps([{ "op": "replace", "path": "/nfStatus", "value": "REGISTERED" }])
        )
        print(response.text)
        if response.status_code == httpx.codes.OK:
            new_nef_profile = NFProfile.from_dict(response.json())
            print(f"new profile {json.dumps(new_nef_profile)}")
        elif response.status_code == httpx.codes.NOT_FOUND:
            print(response.text)
            print("NEF instance not registered")
    return response.status_code

async def nf_status_subscribe():
    nfTypes = [("BSF", "nbsf-management"), ("PCF", "npcf-policyauthorization"), ("UDR", "nudr-dr"), ("UDM", "nudm-sdm")]
    for nfType in nfTypes:
        sub = SubscriptionData(
            nf_status_notification_uri=f"http://{conf.HOSTS['NEF'][0]}:7777/nnrf-nfm/v1/nf-status-notify",
            req_nf_instance_id=conf.NEF_PROFILE.nf_instance_id,
            subscr_cond=SubscrCond(nf_type=nfType[0], service_name=nfType[1]),
            req_nf_type="NEF",
            requester_features="1"
        )
        print(sub)
        async with httpx.AsyncClient(http1=False, http2=True) as client:
            response = await client.post(
                f"http://{conf.HOSTS['NRF'][0]}:7777/nnrf-nfm/v1/subscriptions",
                headers={
                    'Accept': 'application/json,application/problem+json',
                    'Content-Type': 'application/json'
                    },
                data=json.dumps(sub.to_dict())
            )
            print("NF status notify res")
            print(response.text)
            # if response.status_code == httpx.codes.CREATED:
            # [fc5837fc-4753-41ee-a94f-1140a058385d] Subscription created until 2023-08-31T16:40:53.656179+00:00 [duration:86400,validity:86399.997793,patch:43199.998896]
            #     res = subscriptionData.subscription_data_insert(sub, response.headers['location'])
            #     if not res:
            #         print("NF status not subscribed")
    return 201

async def nf_status_unsubscribe(subId):
    async with httpx.AsyncClient(http1=False, http2=True) as client:
        response = await client.delete(
            f"http://{conf.HOSTS['NRF'][0]}:7777/nnrf-nfm/v1/subscriptions/{subId}",
            headers={
                'Accept': 'application/json,application/problem+json',
                'Content-Type': 'application/json-patch+json'
                }
        )
        print(response.text)
    return 1
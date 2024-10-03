import httpx
import json
import datetime
from datetime import datetime, timezone, timedelta
from api.config import conf
from session import async_db
from models.nf_profile import NFProfile
from models.subscription_data import SubscriptionData
from models.subscr_cond import SubscrCond
from models.access_token_req import AccessTokenReq
from models.access_token_err import AccessTokenErr
import crud.nfProfile as nfProfile
import crud.subscriptionData as subscriptionData

async def nrf_discovery():
    hrefs = []
    profiles = []
    collection = async_db['nf_instances']
    collection.delete_many({})

    if conf.CORE == "free5gc":
        for nf in list(conf.NF_SCOPES.keys()):
            async with httpx.AsyncClient(http1=True) as client:
                response = await client.get(
                    f"http://{conf.HOSTS['NRF'][0]}/nnrf-disc/v1/nf-instances",
                    headers=conf.GLOBAL_HEADERS,
                    params={"target-nf-type": nf, "requester-nf-type": "NEF"}
                )
            r = response.json()
            if r["nfInstances"] != None:
                for i in r["nfInstances"]:
                    p = conf.update_values(i)
                    profiles.append(NFProfile.from_dict(p))
                    res = await nfProfile.insert_one(p)

    else:
        for nf in list(conf.NF_SCOPES.keys()):
            conf.logger.info(f"Discovering: {nf}")
            async with httpx.AsyncClient(http1=True if conf.CORE=="free5gc" else False, http2=None if conf.CORE=="free5gc" else True) as client:
                response = await client.get(
                    f"http://{conf.HOSTS['NRF'][0]}/nnrf-nfm/v1/nf-instances",
                    headers=conf.GLOBAL_HEADERS,
                    params={"target-nf-type": nf}
                )
            if response.json():
                r = response.json()
                hrefs += [item["href"] for item in r["_links"]["items"]]

        for href in hrefs:
            async with httpx.AsyncClient(http1=True if conf.CORE=="free5gc" else False, http2=None if conf.CORE=="free5gc" else True) as client:
                response = await client.get(
                    href,
                    headers=conf.GLOBAL_HEADERS
                )
                if response.json():
                    r = response.json()
                    profiles.append(NFProfile.from_dict(r))
                    res = await nfProfile.insert_one(r)
    
    conf.set_nf_endpoints(profiles)

async def nrf_get_access_token():
    for key, scope in conf.NF_SCOPES.items():
        mcc = conf.PLMN[0:3]
        mnc = conf.PLMN[3:] if len(conf.PLMN[3:] == 3) else "0"+conf.PLMN[3:]
        access_token_req = AccessTokenReq(
            grant_type="client_credentials",
            nf_instance_id=conf.API_UUID,
            nf_type="NEF",
            target_nf_type=key,
            target_nf_set_id=f"set<Set ID>.{key.lower()}set.5gc.mnc{mnc}.mcc{mcc}", # st id in NF profiles
            scope=scope,
        )
        async with httpx.AsyncClient(http1=True if conf.CORE=="free5gc" else False, http2=None if conf.CORE=="free5gc" else True) as client:
            response = await client.post(
                f"http://{conf.HOSTS['NRF'][0]}/oauth2/token",
                headers={'Accept': 'application/json,application/problem+json', 'Content-Type': 'application/x-www-form-urlencoded'},
                data=json.dumps(access_token_req.to_dict())
            )
            if response.status_code == httpx.codes.BAD_REQUEST:
                err = AccessTokenErr.from_dict(response.json())
                conf.logger.info(err)
    return response.status_code

async def nf_register():
    async with httpx.AsyncClient(http1=True if conf.CORE=="free5gc" else False, http2=None if conf.CORE=="free5gc" else True) as client:
        response = await client.put(
            f"http://{conf.HOSTS['NRF'][0]}/nnrf-nfm/v1/nf-instances/"+conf.NEF_PROFILE.nf_instance_id,
            headers={
                'Accept': 'application/json,application/problem+json',
                'Content-Type': 'application/json'
                },
            data = json.dumps(conf.NEF_PROFILE.to_dict())
        )
        if response.status_code == httpx.codes.CREATED:
            conf.logger.info(f"[{conf.NEF_PROFILE.nf_instance_id}] NF registerd [Heartbeat:{conf.NEF_PROFILE.heart_beat_timer}s]")
        else:
            conf.logger.info(response.text)
    return response

async def nf_update(profile):

    return 1

async def nf_deregister():
    async with httpx.AsyncClient(http1=True if conf.CORE=="free5gc" else False, http2=None if conf.CORE=="free5gc" else True) as client:
        response = await client.delete(
            f"http://{conf.HOSTS['NRF'][0]}/nnrf-nfm/v1/nf-instances/"+conf.NEF_PROFILE.nf_instance_id,
            headers=conf.GLOBAL_HEADERS
        )
        if response.status_code == httpx.codes.NO_CONTENT:
            conf.logger.info(f"[{conf.NEF_PROFILE.nf_instance_id}] NF de-registered")
        if response.status_code == httpx.codes.NOT_FOUND:
            conf.logger.info("NEF instance not registered")

    return response.status_code

async def nf_register_heart_beat():
    async with httpx.AsyncClient(http1=True if conf.CORE=="free5gc" else False, http2=None if conf.CORE=="free5gc" else True) as client:
        response = await client.patch(
            f"http://{conf.HOSTS['NRF'][0]}/nnrf-nfm/v1/nf-instances/"+conf.NEF_PROFILE.nf_instance_id,
            headers={
                'Accept': 'application/json,application/problem+json',
                'Content-Type': 'application/json-patch+json'
                },
            data = json.dumps([{ "op": "replace", "path": "/nfStatus", "value": "REGISTERED" }])
        )
        # if response.status_code == httpx.codes.OK:
        #     new_nef_profile = NFProfile.from_dict(response.json())
        #     conf.logger.info(f"new profile {json.dumps(new_nef_profile)}")
        if response.status_code == httpx.codes.NOT_FOUND:
            conf.logger.info(response.text)
            conf.logger.info("NEF instance not registered")
    return response.status_code

async def nf_status_subscribe(nf_types):
    async with httpx.AsyncClient(http1=True if conf.CORE=="free5gc" else False, http2=None if conf.CORE=="free5gc" else True) as client:
        current_time = datetime.now(timezone.utc)
        validity_time = current_time + timedelta(days=1)
        formatted_time = validity_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        sub = SubscriptionData(
            nf_status_notification_uri=f"http://{conf.HOSTS['NEF'][0]}/nnrf-nfm/v1/subscriptions",
            req_nf_instance_id=conf.NEF_PROFILE.nf_instance_id,
            validity_time=formatted_time,
            req_nf_type="NEF",
            requester_features="1"
        )
        for nf_type in nf_types:
            conf.logger.info(f"{nf_type} status subscribe")
            sub.subscr_cond = SubscrCond(nf_type=nf_type)
            response = await client.post(
                f"http://{conf.HOSTS['NRF'][0]}/nnrf-nfm/v1/subscriptions",
                headers=conf.GLOBAL_HEADERS,
                data=json.dumps(sub.to_dict())
            )
            conf.logger.info(f"Response for {nf_type} status subscribe. status: {response.status_code}")
            conf.logger.info(response.text)
            if response.status_code == httpx.codes.CREATED:
                data = response.json()
                conf.logger.info(f"Response data: {data}")
                try:
                    sub = SubscriptionData.from_dict(data)
                    conf.logger.info(f"{nf_type} Subscription created until {sub.validity_time}")
                    conf.logger.info(f"Resource location: {response.headers['location']}")
                    try:
                        res = await subscriptionData.subscription_data_insert(sub, response.headers['location'])
                    except Exception as e:
                        conf.logger.error(e)
                        if not res:
                            conf.logger.info("Error saving subscription")
                except Exception as e:
                    conf.logger.info("Can't decode response message!")
            else:
                conf.logger.info(f"{nf_type} Subscription not created")

async def nf_status_unsubscribe(subId=None):
    if not subId:
        subs = subscriptionData.subscription_data_get()
        for sub in subs:
            async with httpx.AsyncClient(http1=True if conf.CORE=="free5gc" else False, http2=None if conf.CORE=="free5gc" else True) as client:
                response = await client.delete(
                    f"http://{conf.HOSTS['NRF'][0]}/nnrf-nfm/v1/subscriptions/{sub['subscription_id']}",
                    headers=conf.GLOBAL_HEADERS
                )
        conf.logger.info(response.text)
    else:
        async with httpx.AsyncClient(http1=True if conf.CORE=="free5gc" else False, http2=None if conf.CORE=="free5gc" else True) as client:
            response = await client.delete(
                f"http://{conf.HOSTS['NRF'][0]}/nnrf-nfm/v1/subscriptions/{subId}",
                headers=conf.GLOBAL_HEADERS
            )
            conf.logger.info(response.text)
    return 1
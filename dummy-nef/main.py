from fastapi import FastAPI, Response
from session import async_db, close
import httpx
import logging
import json
from models.nf_profile import NFProfile
from models.amf_create_event_subscription import AmfCreateEventSubscription
from models.amf_event_subscription import AmfEventSubscription
from models.amf_event import AmfEvent
from enums.amf_event_type import AmfEventType
from models.subscription_data import SubscriptionData
import uuid
from api.config import conf
import core.nrf_handler as nrf_handler

app = FastAPI()
logger = logging.getLogger(__name__)
tmp = {}
nrf = "10.103.218.237:7777"
amf = "10.102.17.49:7777"
smf = "10.111.153.168:80"
self_uuid = ""


@app.on_event("startup")
async def startup():
    print("starting up")
    await nrf_handler.nrf_discovery()
    await nrf_handler.nf_deregister()
    print("started")
    
@app.on_event("shutdown")
async def shutdown():
    print("Database reset complete.")
    close()

@app.get("/")
async def read_root():
    return {"Hello": "World"}

@app.get("/core")
async def get_core_nf():
    collection = async_db["nf_instances"]
    insts = []
    async for user in collection.find({}):
        insts.append(user)
    return {'nfs instances': str(insts)}

@app.get("amf-status")
async def amf_comm():
    sub = SubscriptionData("http://10.102.141.12:80/amf-status-callback", str(uuid.uuid4()), subscription_id="1")
    print(json.dumps(sub))
    async with httpx.AsyncClient(http1=False, http2=True) as client:
        response = await client.post(
            "http://"+conf.AMF_IP+"/namf-comm/v1/subscriptions",
            headers={
                'Accept': 'application/json,application/problem+json',
                'Content-Type': 'application/json'
            },
            data = json.dumps(sub)
        )
        print(response.text)
    return response.text

@app.post("/amf-status-callback")
async def amf_status_callback(data: dict):
    try:
        keys = []
        for key in data.keys():
            keys.append(key)
        print(keys)
    except:
        None
    print(str(data))
    sub = SubscriptionData.from_dict(data)
    print(sub.to_str)
    return Response(status_code=204)

@app.get("nrf-register")
async def nrf_register():
    nef_profile = conf.NEF_PROFILE
    async with httpx.AsyncClient(http1=False, http2=True) as client:
        response = await client.put(
            "http://"+nrf+"/nnrf-nfm/v1/nf-instances/"+conf.API_UUID,
            headers={
                'Accept': 'application/json,application/problem+json',
                'Content-Type': 'application/json'
            },
            data = json.dumps(nef_profile)
        )
    print(response.text)
    return response.json()

@app.get("nrf-register-callback")
async def nrf_register_callback():

    return None

@app.get("smf-pdu-session")
async def smf_policy_control():
    #/npcf-/v1
    return None

@app.get("/ip/{nf_type}")
async def get_nf_ip(nf_type: str):
    async with httpx.AsyncClient(http1=False, http2=True) as client:
        response = await client.get(
            "http://"+nrf+"/nnrf-disc/v1/nf-instances",
            headers={'Accept': 'application/json,application/problem+json'},
            params= {"target-nf-type": f"{nf_type.upper()}", "requester-nf-type": "NEF"}
        )
    print(response.text)
    js = response.json()["nfInstances"]
    profiles = []
    for item in js:
        profiles.append(NFProfile.from_dict(item))
    print("deserialized")
    return {"nf instance id" : [pf.nf_instance_id for pf in profiles], "ipv4 address": [pf.ipv4_addresses for pf in profiles]}

@app.get("/amf-sub")
async def test_amf():
    event = AmfEvent(type=AmfEventType.CONNECTIVITY_STATE_REPORT)
    sub = AmfEventSubscription([event], "http://10.102.141.12:80/amf-sub-res", "1", str(uuid.uuid4()), any_ue=True)
    create = AmfCreateEventSubscription(sub)
    create_event = {"AmfCreateEventSubscription": create.to_dict()}
    print("--------------------------------")
    print(json.dumps(create_event))
    async with httpx.AsyncClient(http1=False, http2=True) as client:
        response = await client.post(
            "http://"+conf.AMF_IP+"/namf-comm/v1/subscriptions",
            headers={
                'Accept': 'application/json,application/problem+json',
                'Content-Type': 'application/json'
            },
            data = json.dumps(create_event)
        )
        print(response.text)
    return response.text

@app.get("/nf-register")
async def register_nf():
    async with httpx.AsyncClient(http1=False, http2=True) as client:
        response = await client.put(
            "http://"+nrf+"/nnrf-nfm/v1/nf-instances/"+conf.nef_profile.nf_instance_id,
            headers={'Accept': 'application/json,application/problem+json'}
        )
        print(response.text)
    return response.text

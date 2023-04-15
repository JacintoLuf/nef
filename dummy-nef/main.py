from fastapi import FastAPI, Response
from session import static_client, async_client, close
from init_db import init_db
import httpx
import logging
import json
import logging
from models.nf_profile import NFProfile
from models.nf_profile import NFProfile
from models.amf_create_event_subscription import AmfCreateEventSubscription
from models.amf_event_subscription import AmfEventSubscription
from models.amf_event import AmfEvent
from enums.amf_event_type import AmfEventType
from models.amf_event_notification import AmfEventNotification
import uuid

app = FastAPI()
logger = logging.getLogger(__name__)
nef_profile = NFProfile()
tmp = {}
nrf = "10.106.127.186:80"
amf = "10.111.27.77:80"
smf = "10.111.153.168:80"
self_uuid = ""


@app.on_event("startup")
async def startup():
    try:
        db = async_client
        collection = db["nf_instances"]
        init_db(db)
        uuids = []
        instances = []
        async with httpx.AsyncClient(http1=False, http2=True) as client:
            response = await client.get(
                "http://"+nrf+"/nnrf-nfm/v1/nf-instances",
                headers={'Accept': 'application/json'}
            )
            logger.debug("resonse code: %s", response.status_code)
            j = json.loads(response.text)
            uuids = [i["href"].split('/')[-1] for i in j["_links"]["items"]]

            while True:
                self_uuid = str(uuid.uuid4())
                if self_uuid not in uuids:
                    break

        async with httpx.AsyncClient(http1=False, http2=True) as client:
            for id in uuids:
                response = await client.get(
                    "http://"+nrf+"/nnrf-nfm/v1/nf-instances/"+id,
                    headers={'Accept': 'application/json'}
                )
                #instances.append(json.loads(response.text))
                instances.append(response.json())
                result = collection.insert_one(json.loads(response.text))

    except Exception as e:
        logger.error(e)
        print(e)
        raise e
    
@app.on_event("shutdown")
async def shutdown():
    print("Database reset complete.")
    close()

@app.get("/")
async def read_root():
    #return {"Hello": "World"}
    event = AmfEvent(type=AmfEventType.CONNECTIVITY_STATE_REPORT, immediate_flag=True)
    sub = AmfEventSubscription([event], "http://10.102.141.12:80/amf-sub-res", "1", self_uuid, any_ue=True)
    create = AmfCreateEventSubscription(sub)
    create_event = {"AmfCreateEventSubscription": create.to_dict()}
    create_event2 = {"amfCreateEventSubscription": create.to_dict()}
    print("--------------------------------")
    print(json.dumps(create_event))
    print("--------------------------------")
    print(json.dumps(create.to_dict()))
    async with httpx.AsyncClient(http1=False, http2=True) as client:
        response = await client.post(
            "http://"+amf+"/namf-comm/v1/subscriptions/",
            headers={
                'Accept': 'application/json,application/problem+json',
                'Content-Type': 'application/json'
            },
            data = json.dumps(create_event)
        )
        print(response.text)
    async with httpx.AsyncClient(http1=False, http2=True) as client:
        response = await client.post(
            "http://"+amf+"/namf-comm/v1/subscriptions/",
            headers={
                'Accept': 'application/json,application/problem+json',
                'Content-Type': 'application/json'
            },
            data = json.dumps(create_event2)
        )
        print(response.text)
    async with httpx.AsyncClient(http1=False, http2=True) as client:
        response = await client.post(
            "http://"+amf+"/namf-comm/v1/subscriptions/",
            headers={
                'Accept': 'application/json,application/problem+json',
                'Content-Type': 'application/json'
            },
            data = json.dumps(create.to_dict())
        )
        print(response.text)
    return response.text

@app.get("/users")
async def get_users():

    collection = async_client["users"]
    users = []
    async for user in collection.find({}):
        users.append(user)
    return str(user)

@app.get("/ip/{nf_type}")
async def get_nf_ip(nf_type: str):

    async with httpx.AsyncClient(http1=False, http2=True) as client:
        response = await client.get(
            "http://"+nrf+"/nnrf-disc/v1/nf-instances",
            headers={'Accept': 'application/json,application/problem+json'},
            params= {"target-nf-type": f"{nf_type.upper()}", "requester-nf-type": "NEF"}
        )
    js = response.json()["nfInstances"]
    profiles = []
    for item in js:
        profiles.append(NFProfile.from_dict(item))
    print("deserialized")
    return {"nf instance id" : [pf.nf_instance_id for pf in profiles], "ipv4 address": [pf.ipv4_addresses for pf in profiles]}

@app.get("/amf-sub")
async def test_amf():
    event = AmfEvent(type=AmfEventType.CONNECTIVITY_STATE_REPORT, immediate_flag=True)
    sub = AmfEventSubscription([event], "http://10.102.141.12:80/amf-sub-res", "1", self_uuid, any_ue=True)
    create = AmfCreateEventSubscription(sub)
    #print(json.dumps(create.to_dict()))
    async with httpx.AsyncClient(http1=False, http2=True) as client:
        response = await client.put(
            "http://"+nrf+"/namf-comm/v1/subscriptions/",
            headers={'Accept': 'application/json,application/problem+json'},
            #data = '{"AmfEventSubscription": {"eventList": [{"type": "CONNECTIVITY_STATE_REPORT","immediateFlag": true}],"notifyUri": "http://10.102.141.12:80/amf-sub-res","notifyCorrelationId": "1","nfId": "5343ae63-424f-412d-8ccb-1677a20c8bcf"}}'
            #data = '{"AmfCreateEventSubscription" :{"AmfEventSubscription": {"eventList": [{"type": "CONNECTIVITY_STATE_REPORT","immediateFlag": true}],"notifyUri": "http://10.102.141.12:80/amf-sub-res","notifyCorrelationId": "1","nfId": "5343ae63-424f-412d-8ccb-1677a20c8bcf"}}}'
            data = json.dumps(create.to_dict())
        )
        print(response.text)
    try:
        keys = []
        for key in response.json().keys():
            keys.append(key)
        print(keys)
    except:
        None
    return response.text

@app.post("/amf-sub-res")
async def test_amf_res(data: dict):
    try:
        keys = []
        for key in data.keys():
            keys.append(key)
        print(keys)
    except:
        None
    print(str(data))
    sub = AmfEventSubscription.from_dict(data)
    print(sub.to_str)
    return Response(status_code=204)

@app.get("/nf-register")
async def register_nf():
    async with httpx.AsyncClient(http1=False, http2=True) as client:
        response = await client.put(
            "http://"+nrf+"/nnrf-nfm/v1/nf-instances/"+nef_profile.nf_instance_id,
            headers={'Accept': 'application/json,application/problem+json'}
        )
        print(response.text)
    return response.text

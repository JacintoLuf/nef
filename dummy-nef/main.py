import json
from fastapi import FastAPI, Request, Response
from fastapi_utils.tasks import repeat_every
from session import async_db
import httpx
import logging
from api.config import conf
from models.traffic_influ_sub import TrafficInfluSub
import core.nrf_handler as nrf_handler
import core.bsf_handler as bsf_handler
import core.pcf_handler as pcf_handler
import core.udm_handler as udm_handler
import core.udr_handler as udr_handler
import crud.trafficInfluSub

app = FastAPI()
logger = logging.getLogger(__name__)


@app.on_event("startup")
async def startup():
    print("starting up")
    print(f"api uuid: {conf.NEF_PROFILE.nf_instance_id}")
    res = await nrf_handler.nrf_discovery()
    res = await nrf_handler.nf_register()
    if res == httpx.codes.CREATED:
        await nrf_heartbeat()
    await bsf_handler.bsf_management_discovery()
    print("started")

@repeat_every(seconds=conf.NEF_PROFILE.heart_beat_timer - 2)
async def nrf_heartbeat():
    await nrf_handler.nf_register_heart_beat()
    
@app.on_event("shutdown")
async def shutdown():
    print("shuting down...")
    nrf_handler.nf_deregister()

@app.get("/")
async def read_root():
    collection = async_db["nf_instances"]
    insts = []
    async for user in collection.find({}):
        insts.append(user)
    return {'nfs instances': str(insts)}

@app.post("/ti_create")
async def ti_create(ipv4: str=None):
    #uri: /3gpp-traffic-influence/v1/{afId}/subscriptions
    #res code: 201
    #map ipv6 addr to ipv6 prefix
    data = TrafficInfluSub(ipv4_addr=ipv4)
    traffic_sub = TrafficInfluSub.from_dict(json.loads(data))
    status_code, res = bsf_handler.bsf_management_discovery(traffic_sub)
    return {'res': res}

@app.put("/ti_update")
async def ti_put():
    #uri: /3gpp-traffic-influence/v1/{afId}/subscriptions/{subId}
    #res code: 200 
    return 200

@app.patch("/ti_update")
async def ti_patch():
    #uri: /3gpp-traffic-influence/v1/{afId}/subscriptions/{subId}
    #res code: 200 
    return 200

@app.post("/ti_delete")
async def ti_delete():
    #uri: /3gpp-traffic-influence/v1/{afId}/subscriptions/{subId}
    #res code: 204 
    return 204
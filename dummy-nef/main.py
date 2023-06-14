import json
import httpx
import logging
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi_utils.tasks import repeat_every
from models.app_session_context_req_data import AppSessionContextReqData
from session import async_db
from api.config import conf
from models.traffic_influ_sub import TrafficInfluSub
from models.pcf_binding import PcfBinding
import core.nrf_handler as nrf_handler
import core.bsf_handler as bsf_handler
import core.pcf_handler as pcf_handler
import crud.appSessionContext as appSessionContext

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

@app.get("/ti_create")
async def ti_create(ipv4: str=None):
    #uri: /3gpp-traffic-influence/v1/{afId}/subscriptions
    #res code: 201
    #map ipv6 addr to ipv6 prefix
    data = TrafficInfluSub(ipv4_addr=ipv4)
    # try:
    #     traffic_sub = TrafficInfluSub.from_dict(json.loads(data))
    # except Exception as e:
    #     raise HTTPException(status_code=httpx.codes.BAD_REQUEST, detail="cannot parse HTTP message")
    response: httpx.Response = await bsf_handler.bsf_management_discovery(data)
    if response.status_code != httpx.codes.OK:
            return response
    pcf_binding = PcfBinding.from_dict(response.json())
    # traffic_influ_sub_attr = vars(TrafficInfluSub())
    # req_data = AppSessionContextReqData()
    #print(traffic_influ_sub_attr.items())
    # print("----------------------matching attr-----------------------")
    # for attr_name in traffic_influ_sub_attr.items():
    #     if hasattr(req_data, attr_name):
    #         print(attr_name)
    # print("----------------------------------------------------------")
    response = await pcf_handler.pcf_policy_authorization_create([ip.to_str() for ip in pcf_binding.pcf_ip_end_points])
    # if response:
    #     appSessionContext.insert_one(response)
    return 201

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
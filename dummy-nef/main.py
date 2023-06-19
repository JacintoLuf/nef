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
import core.udm_handler as udm_handler
import crud.trafficInfluSub as trafficInfluSub
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

@app.get("/3gpp-traffic-influence/v1/{afId}/subscriptions", responses={201: {"description": "Created"}})
async def ti_create(afId, data: Request):
    #data = TrafficInfluSub(ipv4_addr=ipv4)
    if not afId:
        raise HTTPException(httpx.codes.BAD_REQUEST, detail="Invalid AF ID")

    try:
        traffic_sub = TrafficInfluSub.from_dict(data.json())
    except:
        raise HTTPException(httpx.codes.BAD_REQUEST, detail="cannot parse HTTP message")
    
    if traffic_sub.notification_destination and not traffic_sub.subscribed_events:
        raise HTTPException(httpx.codes.BAD_REQUEST, detail="cannot parse HTTP message")
    
    if traffic_sub.any_ue_ind:
        print("any UE")
    elif traffic_sub.ipv4_addr or traffic_sub.ipv6_addr or traffic_sub.mac_addr:
        response: httpx.Response = await bsf_handler.bsf_management_discovery(data)
        if response.status_code != httpx.codes.OK:
                return response
        response = await pcf_handler.pcf_policy_authorization_create([ip['ipv4Address'] for ip in pcf_binding.pcf_ip_end_points], data)
    elif traffic_sub.gpsi:
        translation_res = udm_handler.udm_sdm_id_translation(traffic_sub.gpsi)
    elif traffic_sub.external_group_id:
        translation_res = udm_handler.udm_sdm_group_identifiers_translation(traffic_sub.external_group_id)

    response: httpx.Response = await bsf_handler.bsf_management_discovery(data)
    if response.status_code != httpx.codes.OK:
            return response
    
    pcf_binding = PcfBinding.from_dict(response.json())
    
    response = await pcf_handler.pcf_policy_authorization_create([ip['ipv4Address'] for ip in pcf_binding.pcf_ip_end_points], data)

    #sub_id = trafficInfluSub.traffic_influence_subscription_post(trafficInfluSub)
    #data.__self = f"http://{conf.HOSTS['NEF'][0]}:80/3gpp-trafficInfluence/v1/{afId}/subscriptions/{sub_id}"
    # if response:
    #     appSessionContext.insert_one(response)
    return 201

@app.post("/pcf-policy-authorization-callback")
async def pcf_callback(data):
    print(data)
    return 200

@app.get("/3gpp-traffic-influence/v1/{afId}/subscriptions/{subId}")
async def ti_get():
    #uri: /3gpp-traffic-influence/v1/{afId}/subscriptions/{subId}
    #res code: 200 
    return 200

@app.put("/3gpp-traffic-influence/v1/{afId}/subscriptions/{subId}", responses={200: {"description": "Updated"}})
async def ti_put():
    #uri: /3gpp-traffic-influence/v1/{afId}/subscriptions/{subId}
    #res code: 200
    return 200

@app.patch("/3gpp-traffic-influence/v1/{afId}/subscriptions/{subId}", responses={200: {"description": "Updated"}})
async def ti_patch():
    #uri: /3gpp-traffic-influence/v1/{afId}/subscriptions/{subId}
    #res code: 200 
    return 200

@app.delete("/3gpp-traffic-influence/v1/{afId}/subscriptions/{subId}", responses={204: {"description": "Deleted"}})
async def ti_delete(afId: str, subId: str):
    #uri: /3gpp-traffic-influence/v1/{afId}/subscriptions/{subId}
    #res code: 204
    res = pcf_handler.pcf_policy_authorization_delete(afId, subId)
    return 204
import httpx
from main import app
from fastapi import APIRouter, Request, Response, HTTPException
from api.config import conf
import json
import httpx
from api.config import conf
from fastapi import APIRouter, Request, Response, HTTPException
from models.pcf_binding import PcfBinding
from models.event_notification import EventNotification
from models.nsmf_event_exposure_notification import NsmfEventExposureNotification
import core.af_handler as af_handler
import core.bsf_handler as bsf_handler
import core.pcf_handler as pcf_handler
import crud.nfProfile as nfProfile
import crud.trafficInfluSub as trafficInfluSub
import crud.asSessionWithQoSSub as asSessionWithQoSSub
import crud.monitoringEventSubscription as monitoringEventSubscription
from session import clean_db


router = APIRouter()

@router.get("/")
async def read_root():
    insts = await nfProfile.get_all()
    return {'nfs instances': str(insts)}

async def send_notification(data: str, link: str):
    async with httpx.AsyncClient(http1=False, http2=True) as client:
        response = await client.post(
            link,
            headers=conf.GLOBAL_HEADERS,
            data=json.dumps(data)
        )
        conf.logger.info(response.text)

@router.get("/ue/{ipv4}")
async def ue_info(ipv4: str):
    supi = None
    if "BSF" in conf.HOSTS.keys():
        bsf_params = {'ipv4Addr': ipv4}

        res = await bsf_handler.bsf_management_discovery(bsf_params)
        if res['code'] != httpx.codes.OK:
            raise HTTPException(status_code=httpx.codes.NOT_FOUND, detail="Session not found")
        pcf_binding = PcfBinding.from_dict(res['response'])
        if not pcf_binding.supi:
            raise HTTPException(status_code=httpx.codes.NOT_FOUND, detail="UE_ID_NOT_AVAILABLE")
        conf.logger.info(f"SUPI: {pcf_binding.supi}")
        supi = pcf_binding.supi
        
    params = {'dataset-names': ['AMF', 'SM']}
    res = ""
    async with httpx.AsyncClient(http1=True if conf.CORE=="free5gc" else False, http2=None if conf.CORE=="free5gc" else True) as client:
        response = await client.get(
            f"http://{conf.HOSTS['UDM'][0]}/nudm-sdm/v2/{supi}/am-data",
            headers={'Accept': 'application/json,application/problem+json'}
        )
        res += response.text
        conf.logger.info(f"am data v2:\n {response.text}")
    res += "\n-----------------------------------------------------\n"
    async with httpx.AsyncClient(http1=True if conf.CORE=="free5gc" else False, http2=None if conf.CORE=="free5gc" else True) as client:
        response = await client.get(
            f"http://{conf.HOSTS['UDM'][0]}/nudm-sdm/v2/{supi}/sm-data",
            headers={'Accept': 'application/json,application/problem+json'}
        )
        res += response.text
        conf.logger.info(f"sm data v2:\n {response.text}")
    res += "\n-----------------------------------------------------\n"
    async with httpx.AsyncClient(http1=True if conf.CORE=="free5gc" else False, http2=None if conf.CORE=="free5gc" else True) as client:
        response = await client.get(
            f"http://{conf.HOSTS['UDM'][0]}/nudm-sdm/v2/{supi}",
            headers={'Accept': 'application/json,application/problem+json'},
            params=params
        )
        res += response.text
        conf.logger.info(f"ue data v2:\n {response.text}")
    return res

#-----------------------------callback endpoints---------------------------------
@router.post("/nnef-callback/amf-event-sub-callback")
async def amf_evt_sub_callback(request: Request):
    conf.logger.info(request.method)
    conf.logger.info(request.body)

@router.post("/nnef-callback/udm-event-sub-callback")
async def udm_evt_sub_callback(request: Request):
    conf.logger.info("endpoint: /nnef-callback/udm-event-sub-callback")
    conf.logger.info(request.method)
    conf.logger.info(request.headers)
    conf.logger.info(request.body)
    # mon_evt_rep = MonitoringEventReport()
    return Response(status_code=httpx.codes.OK, headers=conf.GLOBAL_HEADERS)

@router.post("/nnef-callback/nrf_subscription_update")
async def nrf_notif(request: Request):
    conf.logger.info("endpoint: /nnef-callback/nrf_subscription_update")
    conf.logger.info(request.method)
    conf.logger.info(request.body)

@router.post("/nnef-callback/smf_up_path_change/{subId}")
# @router.post("/up_path_change")
async def up_path_chg_notif(subId: str, request: Request):
# async def up_path_chg_notif(request: Request):
    conf.logger.info("endpoint: /up_path_change")
    conf.logger.info(request.text)
    try:
        data = await request.json()
        smf_notif = NsmfEventExposureNotification(data)
        notifs = smf_notif.event_notifs
    except Exception as e:
        conf.logger.info(e.__str__)
    for notif in notifs:
        evt_notif = EventNotification(
            dnai_chg_type=notif.dnai_chg_type,
            source_traffic_route=notif.source_tra_routing,
            subscribed_event=notif.event,
            target_traffic_route=notif.target_tra_routing,
            source_dnai=notif.source_dnai,
            target_dnai=notif.target_dnai,
            gpsi=notif.gpsi,
            src_ue_ipv4_addr=notif.source_ue_ipv4_addr,
            src_ue_ipv6_prefix=notif.source_ue_ipv6_prefix,
            tgt_ue_ipv4_addr=notif.target_ue_ipv4_addr,
            tgt_ue_ipv6_prefix=notif.target_ue_ipv6_prefix,
            ue_mac=notif.ue_mac,
        )
        res = await af_handler.af_up_path_chg_notif(subId, evt_notif)
    return Response(status_code=httpx.codes.NO_CONTENT)

@router.post("/nnef-callback/pcf_qos_notif/{id}")
async def nrf_notif(id: str, request: Request):
    conf.logger.info("endpoint: /nnef-callback/pcf_qos_notif")
    conf.logger.info(request.method)
    conf.logger.info(request.body)



#---------------------monitoring-event------------------------
@router.get("/monget")
async def mon_get():
    conf.logger.info("getting all subscription")
    res = await monitoringEventSubscription.get()
    if not res:
        return {'subs': []}
    return {'subs': res}

@router.get("/monget/{subId}")
async def mon_get(subId: str=None):
    if not subId:
        raise HTTPException(status_code=httpx.codes.BAD_REQUEST, detail="Subscription ID not provided!")
    conf.logger.info(f"getting subscription: {subId}")
    res = await monitoringEventSubscription.get(subId)
    if not res:
        return {'subs': []}
    return {'subs': res}

@router.get("/mondelete/{subId}")
async def mon_del(subId: str):
    try:
        res = await monitoringEventSubscription.get(subId)
        if not res:
            raise HTTPException(status_code=httpx.codes.NOT_FOUND, detail="Subscription not found!")
        else:
            contextId = res['location'].split('/')[-1]
            async with httpx.AsyncClient(http1=True if conf.CORE=="free5gc" else False, http2=None if conf.CORE=="free5gc" else True) as client:
                res = await client.post(
                    f"{contextId}/delete",
                    headers={'Accept': 'application/json,application/problem+json'},
                )
                conf.logger.info(f"Response {res.status_code} for deleting app session. Content:")
                conf.logger.info(res.text)
            if res.status_code != httpx.codes.NO_CONTENT:
                conf.logger.info("Context not found!")
                raise HTTPException(status_code=httpx.codes.NOT_FOUND, detail="Subscription not found!")
            res = await monitoringEventSubscription.delete(subId)
            if res == 1:
                return Response(status_code=httpx.codes.NO_CONTENT)
    except Exception as e:
        raise HTTPException(status_code=httpx.codes.INTERNAL_SERVER_ERROR, detail=e.__str__)
    

#---------------------traffic-influence------------------------
@router.get("/tiget")
async def tiget():
    conf.logger.info("getting all subscription")
    res = await trafficInfluSub.get()
    if not res:
        return {'subs': []}
    return {'subs': res}

@router.get("/tiget/{subId}")
async def tiget(subid: str=None):
    if not subid:
        raise HTTPException(status_code=httpx.codes.BAD_REQUEST, detail="Subscription ID not provided!")
    conf.logger.info(f"getting subscription: {subid}")
    res = await trafficInfluSub.get(subId=subid)
    if not res:
        return {'subs': []}
    return {'subs': res}

@router.get("/tidelete/{subId}")
async def tidelete(subId: str):
    conf.logger.info(f"deleting: {subId}")
    res = await trafficInfluSub.get(subId)
    if not res:
        raise HTTPException(status_code=httpx.codes.NOT_FOUND, detail="Subscription not found!")
    else:
        contextId = res['location'].split('/')[-1]
        res = await pcf_handler.pcf_policy_authorization_delete(contextId)
        if res.status_code != httpx.codes.NO_CONTENT:
            conf.logger.info("Context not found!")

        res = await trafficInfluSub.delete(subId)
        if res == 1:
            return Response(status_code=httpx.codes.NO_CONTENT)
    raise HTTPException(status_code=httpx.codes.INTERNAL_SERVER_ERROR, detail="Failed to delete subscription")


#---------------------as-session-with-qos------------------------
@router.get("/qget")
async def qget():
    conf.logger.info("getting all subscription")
    res = await asSessionWithQoSSub.get()
    if not res:
        return {'subs': []}
    return {'subs': res}

@router.get("/qget/{subId}")
async def qget(subId: str=None):
    if not subId:
        raise HTTPException(status_code=httpx.codes.BAD_REQUEST, detail="Subscription ID not provided!")
    conf.logger.info(f"getting subscription: {subId}")
    res = await asSessionWithQoSSub.get(subId)
    if not res:
        return {'subs': []}
    return {'subs': res}

@router.get("/qdelete/{subId}")
async def qo_s_delete(subId: str):
    res = await asSessionWithQoSSub.get(subId)
    if not res:
        raise HTTPException(status_code=httpx.codes.NOT_FOUND, detail="Subscription not found!")
    else:
        contextId = res['location'].split('/')[-1]
        res = await pcf_handler.pcf_policy_authorization_delete(contextId)
        if res.status_code != httpx.codes.NO_CONTENT:
            conf.logger.info("Context not found!")

        res = await asSessionWithQoSSub.delete(subId)
        if res == 1:
            return Response(status_code=httpx.codes.NO_CONTENT)
    raise HTTPException(status_code=httpx.codes.INTERNAL_SERVER_ERROR, detail="Failed to delete subscription")


#----------------------clean db-------------------
#
#
@router.get("/clean")
async def clean():
    res = clean_db()
    if res:
        return {"result": "Database cleaned."}
    else:
        raise HTTPException(status_code=httpx.codes.INTERNAL_SERVER_ERROR, detail="Error cleaning database!")
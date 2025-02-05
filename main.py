import asyncio
import json
import uuid
import httpx
from time import time
from session import clean_db
from api.config import conf
from fastapi import FastAPI, Request, Response, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from fastapi_utils.tasks import repeat_every
from controllers.internal import router as internal_router
from controllers.monitoring_event import router as monitoring_event_router
from controllers.as_session_with_qos import router as as_session_with_qos_router
from controllers.traffic_influence import router as traffic_influence_router
from controllers.ue_id import router as ue_id_router
from models.pcf_binding import PcfBinding
from models.traffic_influ_sub import TrafficInfluSub
from models.event_notification import EventNotification
from models.traffic_influ_sub_patch import TrafficInfluSubPatch
from models.created_ee_subscription import CreatedEeSubscription
from models.monitoring_event_subscription import MonitoringEventSubscription
from models.amf_created_event_subscription import AmfCreatedEventSubscription
from models.nsmf_event_exposure_notification import NsmfEventExposureNotification
from models.as_session_with_qo_s_subscription import AsSessionWithQoSSubscription
import core.af_handler as af_handler
import core.nrf_handler as nrf_handler
import core.amf_handler as amf_handler
import core.bsf_handler as bsf_handler
import core.pcf_handler as pcf_handler
import core.udm_handler as udm_handler
import core.udr_handler as udr_handler
import crud.nfProfile as nfProfile
import crud.trafficInfluSub as trafficInfluSub
import crud.asSessionWithQoSSub as asSessionWithQoSSub
import crud.monitoringEventSubscription as monitoringEventSubscription


async def request_logger(request: Request):
    conf.logger.info(f"METHOD: {request.method}, URL: {request.url}")

app = FastAPI(debug=True, dependencies=[Depends(request_logger)])

# all_routers = [internal_router, monitoring_event_router, traffic_influence_router, as_session_with_qos_router, ue_id_router]
all_routers = [ue_id_router]
for router in all_routers:
    app.include_router(router)

# router = APIRouter(route_class=CustomRouter)
# @app.middleware('http')
# async def req_middleware(request: Request, call_next):
#     print(f"METHOD: {request.method}, URL: {request.url}")
#     conf.logger.info(f"REQUESTED - {request.method}: {request.url}")
#     if request.method in ["POST", "PUT", "PATCH"]:
#         body = await request.body()
#         conf.logger.info(f"body: {body}")
#     response = await call_next(request)
#     return response

@app.exception_handler(Exception)
async def exception_callback(request: Request, exc: Exception):
    conf.logger.info(f"Failed method {request.method} at URL {request.url}.")
    conf.logger.info(f"Exception message is {exc!r}.")


@app.on_event("startup")
async def startup():
    try:
        conf.logger.info("Registering NEF...")
        res = await nrf_handler.nf_register()
        if res.status_code in [httpx.codes.OK, httpx.codes.CREATED, httpx.codes.NO_CONTENT]:
            conf.REGISTERED = True
            await nrf_heartbeat()
        if not conf.REGISTERED:
            conf.logger.info("Registration failed!\nRetrying...")
            await retry_registration()
        conf.logger.info("NF discovery...")
        await nrf_handler.nrf_discovery()
        conf.logger.info("NF status subscribe...")
        await status_subscribe()
        await asyncio.sleep(5)
        conf.logger.info("amf UE event subscription")
        await amf_handler.amf_event_exposure_subscribe()
        conf.logger.info("udm UE event subscription")
        res = await udm_handler.udm_event_exposure_subscribe()
    except Exception as e:
        conf.logger.info(f"Error starting up: {e!r}")
    # TLS dependant
    # conf.logger.info("Getting access token...")
    # res = await nrf_handler.nrf_get_access_token()

@repeat_every(seconds=conf.NEF_PROFILE.heart_beat_timer)
async def nrf_heartbeat():
    res = await nrf_handler.nf_register_heart_beat()
    if res not in [httpx.codes.OK, httpx.codes.CREATED, httpx.codes.NO_CONTENT]:
        conf.logger.info("Heartbeat failed: NF not found. Re-registering...")
        conf.REGISTERED = False

async def retry_registration():
    try:
        while not conf.REGISTERED:
            conf.logger.info("Re-registering NEF...")
            conf.update_uuid()
            res = await nrf_handler.nf_register()
            if res.status_code in [httpx.codes.OK, httpx.codes.CREATED, httpx.codes.NO_CONTENT]:
                conf.logger.info("Re-registration successful.")
                conf.REGISTERED = True
            else:
                conf.logger.info("Re-registration failed. Retrying...")
                await asyncio.sleep(5)
    except Exception as e:
        conf.logger.error(f"Error during re-registration: {e!r}")


@repeat_every(seconds=86400)
async def status_subscribe():
    try:
        await nrf_handler.nf_status_subscribe(list(conf.NF_SCOPES.keys()))
    except Exception as e:
        conf.logger.error(e)

@app.on_event("shutdown")
async def shutdown():
    conf.logger.info("shuting down...")
    await nrf_handler.nf_status_unsubscribe()
    await nrf_handler.nf_deregister()
    # clean_db()

@app.get("/")
async def read_root():
    insts = await nfProfile.get_all()
    return {'nfs instances': str(insts)}

async def send_notification(data: str, link: str):
    conf.logger.info(f"Sending notification to {link}")
    try:
        async with httpx.AsyncClient(http1=False, http2=True) as client:
            response = await client.post(
                link,
                headers=conf.GLOBAL_HEADERS,
                data=json.dumps(data)
            )
            conf.logger.info(response.text)
    except HTTPException as e:
        conf.logger.info(f"Failed to send notification: {e!r}")

@app.get("/ue/{ipv4}")
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
@app.post("/nnef-callback/amf-event-sub-callback")
async def amf_evt_sub_callback(request: Request):
    conf.logger.info(request.method)
    conf.logger.info(request.body)

@app.post("/nnef-callback/udm-event-sub-callback")
async def udm_evt_sub_callback(request: Request):
    conf.logger.info("endpoint: /nnef-callback/udm-event-sub-callback")
    conf.logger.info(request.method)
    conf.logger.info(request.headers)
    conf.logger.info(request.body)
    # mon_evt_rep = MonitoringEventReport()
    return Response(status_code=httpx.codes.OK, headers=conf.GLOBAL_HEADERS)

@app.post("/nnef-callback/nrf_subscription_update")
async def nrf_notif(request: Request):
    conf.logger.info("endpoint: /nnef-callback/nrf_subscription_update")
    conf.logger.info(request.method)
    conf.logger.info(request.body)

@app.post("/nnef-callback/smf_up_path_change/{subId}")
# @app.post("/up_path_change")
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

@app.post("/nnef-callback/pcf_qos_notif/{id}")
async def nrf_notif(id: str, request: Request):
    conf.logger.info("endpoint: /nnef-callback/pcf_qos_notif")
    conf.logger.info(request.method)
    conf.logger.info(request.body)



#---------------------monitoring-event------------------------
@app.get("/monget")
async def mon_get():
    conf.logger.info("getting all subscription")
    res = await monitoringEventSubscription.get()
    if not res:
        return {'subs': []}
    return {'subs': res}

@app.get("/monget/{subId}")
async def mon_get(subId: str=None):
    if not subId:
        raise HTTPException(status_code=httpx.codes.BAD_REQUEST, detail="Subscription ID not provided!")
    conf.logger.info(f"getting subscription: {subId}")
    res = await monitoringEventSubscription.get(subId)
    if not res:
        return {'subs': []}
    return {'subs': res}

@app.get("/mondelete/{subId}")
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


@app.get("/3gpp-monitoring-event/v1/{scsAsId}/subscriptions/{subscriptionId}")
async def mon_evt_subs_get(scsAsId: str, subscriptionId: str):
    start_time = time()
    conf.logger.info(f"Initiating {scsAsId} Monitoring Event subscription retrieval {subscriptionId}")
    res = await monitoringEventSubscription.monitoring_event_subscriptionscription_get(scsAsId, subscriptionId)
    if not res:
        raise HTTPException(status_code=httpx.codes.NOT_FOUND, detail="content not found")
    end_time = (time() - start_time) * 1000
    headers = conf.GLOBAL_HEADERS
    headers.update({'X-ElapsedTime-Header': str(end_time)})
    return Response(content=res, headers=headers, status_code=httpx.codes.OK)

@app.get("/3gpp-monitoring-event/v1/{scsAsId}/subscriptions")
async def mon_evt_subs_get_all(scsAsId: str):
    start_time = time()
    conf.logger.info(f"Initiating {scsAsId} Monitoring Event subscriptions retrieval")
    res = await monitoringEventSubscription.monitoring_event_subscriptionscription_get(scsAsId)
    if not res:
        raise HTTPException(status_code=httpx.codes.NOT_FOUND, detail="content not found")
    end_time = (time() - start_time) * 1000
    headers = conf.GLOBAL_HEADERS
    headers.update({'X-ElapsedTime-Header': str(end_time)})
    return Response(content=res, headers=headers, status_code=httpx.codes.OK)

@app.post("/3gpp-monitoring-event/v1/{scsAsId}/subscriptions")
async def mon_evt_subs_post(scsAsId: str, data: Request, background_tasks: BackgroundTasks):
    start_time = time()
    conf.logger.info(f"Initiating {scsAsId} Monitoring Event subscription creation")

    try:
        data_dict = await data.json()
        mon_evt_sub = MonitoringEventSubscription.from_dict(data_dict)
    except ValueError as e:
        raise HTTPException(status_code=httpx.codes.BAD_REQUEST, detail=f"Failed to parse message. Err: {e.__str__}")
    except Exception as e:
        raise HTTPException(status_code=httpx.codes.INTERNAL_SERVER_ERROR, detail=e.__str__)
    
    if mon_evt_sub.monitoring_type == "LOCATION_REPORTING" and mon_evt_sub.accuracy not in ["CGI_ECGI","TA_RA","GEO_AREA","CIVIC_ADDR"]:
        raise HTTPException(httpx.codes.BAD_REQUEST, detail="Invalid Accuracy value! Valid values: CGI_ECGI, TA_RA, GEO_AREA and CIVIC_ADDR")
    if mon_evt_sub.rep_period and mon_evt_sub.monitoring_type not in ["LOCATION_REPORTING", "NUMBER_OF_UES_IN_AN_AREA", "NUM_OF_REGD_UES", "NUM_OF_ESTD_PDU_SESSIONS"]:
        raise HTTPException(httpx.codes.BAD_REQUEST, detail="Periodic Reporting not supported for this Monitoring type! Valid Monitoring types: LOCATION_REPORTING, NUMBER_OF_UES_IN_AN_AREA, NUM_OF_REGD_UES, NUM_OF_ESTD_PDU_SESSIONS")
    if mon_evt_sub.monitoring_type in ["LOCATION_REPORTING", "NUMBER_OF_UES_IN_AN_AREA"] and not mon_evt_sub.location_type:
        raise HTTPException(httpx.codes.BAD_REQUEST, detail="Cannot parse message. Must include Location Type!")
    if mon_evt_sub.location_type == "LAST_KNOWN_LOCATION" and mon_evt_sub.maximum_number_of_reports != 1:
        raise HTTPException(httpx.codes.BAD_REQUEST, detail="Cannot parse message. One-time reporting Monitoring type")
    if mon_evt_sub.monitoring_type in ["PDN_CONNECTIVITY_STATUS", " DOWNLINK_DATA_DELIVERY_STATUS"] and not (mon_evt_sub.dnn or mon_evt_sub.snssai):
        #####################################
        raise HTTPException(httpx.codes.BAD_REQUEST, detail="Cannot parse message. Monitoring type must contain Dnn and/or Snssai")
    if mon_evt_sub.maximum_number_of_reports == 1 and mon_evt_sub.monitor_expire_time:
        raise HTTPException(status_code=httpx.codes.BAD_REQUEST, detail='Cannot parse message. One time reporting must not contain expire time')
    if (mon_evt_sub.reachability_type == "SMS" and mon_evt_sub.monitoring_type == "UE_REACHABILITY") or (mon_evt_sub.location_type == "LAST_KNOWN_LOCATION" and mon_evt_sub.monitoring_type == "LOCATION_REPORTING"):
        if mon_evt_sub.maximum_number_of_reports != 1:
            raise HTTPException(status_code=httpx.codes.BAD_REQUEST, detail='Only one-time reporting supported for this event.')
    if mon_evt_sub.location_type or mon_evt_sub.accuracy or mon_evt_sub.minimum_report_interval:
        if not ((mon_evt_sub.external_id is not None)^(mon_evt_sub.msisdn is not None)^(mon_evt_sub.ipv4_addr is not None)^(mon_evt_sub.ipv6_addr is not None)^(mon_evt_sub.external_group_id is not None)):
            raise HTTPException(httpx.codes.BAD_REQUEST, detail='One of the properties "externalId", "msisdn", "ipv4Addr", "ipv6Addr" or "externalGroupId" shall be included for features "Location_notification" and "Communication_failure_notification"')
    if mon_evt_sub.location_type or mon_evt_sub.accuracy or mon_evt_sub.minimum_report_interval or mon_evt_sub.max_rpt_expire_intvl or mon_evt_sub.sampling_interval or mon_evt_sub.reporting_loc_est_ind or mon_evt_sub.linear_distance or mon_evt_sub.loc_qo_s or mon_evt_sub.svc_id or mon_evt_sub.ldr_type or mon_evt_sub.velocity_requested or mon_evt_sub.max_age_of_loc_est or mon_evt_sub.loc_time_window or mon_evt_sub.supported_gad_shapes or mon_evt_sub.code_word or mon_evt_sub.location_area5_g:
        if not ((mon_evt_sub.external_id is not None)^(mon_evt_sub.msisdn is not None)^(mon_evt_sub.external_group_id is not None)):
            raise HTTPException(httpx.codes.BAD_REQUEST, detail='One of the properties "externalId", "msisdn" or "externalGroupId" shall be included for feature "eLCS"')
    if mon_evt_sub.monitoring_type == "NUMBER_OF_UES_IN_AN_AREA" and mon_evt_sub.maximum_number_of_reports != 1:
        raise HTTPException(status_code=httpx.codes.BAD_REQUEST, detail='Only one-time reporting supported for this event.')

    _id = str(uuid.uuid4().hex)
    while await monitoringEventSubscription.check_id(_id):
        _id = str(uuid.uuid4().hex)

    if mon_evt_sub.monitoring_type in ['LOSS_OF_CONNECTIVITY','UE_REACHABILITY','LOCATION_REPORTING','CHANGE_OF_IMSI_IMEI_ASSOCIATION','ROAMING_STATUS','COMMUNICATION_FAILURE','PDN_CONNECTIVITY_STATUS','AVAILABILITY_AFTER_DDN_FAILURE','API_SUPPORT_CAPABILITY']:
        conf.logger.info(f"Creating UDM event exposure subscription for {mon_evt_sub.monitoring_type}")
        res = await udm_handler.udm_event_exposure_subscription_create(mon_evt_sub, scsAsId, _id)
        data = res.json()
        created_evt = CreatedEeSubscription.from_dict(data)
        if created_evt.event_reports:
            conf.logger.info(f"Creating event report for {mon_evt_sub.monitoring_type}")
            mon_evt_sub.monitoring_event_report = af_handler.af_imidiate_report(mon_rep=created_evt.event_reports)
    if mon_evt_sub.monitoring_type in ['NUMBER_OF_UES_IN_AN_AREA', 'REGISTRATION_STATE_REPORT', 'CONNECTIVITY_STATE_REPORT']:
        conf.logger.info(f"Creating AMF event exposure subscription for {mon_evt_sub.monitoring_type}")
        if mon_evt_sub.external_group_id:
            internal_id = await udm_handler.udm_sdm_group_identifiers_translation(mon_evt_sub.external_group_id)
            if internal_id:
                res = await amf_handler.amf_event_exposure_subscription_create(mon_evt_sub, scsAsId, internal_id, _id)
        else:
            res = await amf_handler.amf_event_exposure_subscription_create(mon_evt_sub, scsAsId, _id=_id)
        data = res.json()
        created_evt = AmfCreatedEventSubscription.from_dict(data_dict)
        if created_evt.report_list:
            conf.logger.info(f"Creating event report for {mon_evt_sub.monitoring_type}")
            mon_evt_sub.monitoring_event_report = af_handler.af_imidiate_report(amf_evt_rep=created_evt.report_list)

    if res.status_code == httpx.codes.CREATED:
        headers = conf.GLOBAL_HEADERS
        if mon_evt_sub.request_test_notification:
            test_notif = {'subscription': mon_evt_sub.notification_destination}
            background_tasks.add_task(send_notification, test_notif, mon_evt_sub.notification_destination)
        if res.headers['location']:
            inserted = monitoringEventSubscription.monitoring_event_subscriptionscription_insert(scsAsId, mon_evt_sub, res.headers['location'], _id)
            location = f"http://{conf.HOSTS['NEF'][0]}/3gpp-monitoring-event/v1/{scsAsId}/subscriptions/{inserted}"
            mon_evt_sub._self = location
            #mon_evt_sub.monitor_expire_time = 1 hr
            headers = conf.GLOBAL_HEADERS
            headers['location'] = location
        end_time = (time() - start_time) * 1000
        headers.update({'X-ElapsedTime-Header': str(end_time)})
        return Response(status_code=httpx.codes.CREATED, headers=headers, content=mon_evt_sub.to_dict())
    else:
        return Response(status_code=res.status_code, headers=conf.GLOBAL_HEADERS, content="Subscription creation failed!")
        


@app.put("/3gpp-monitoring-event/v1/{scsAsId}/subscriptions/{subscriptionId}")
async def mon_evt_sub_put(scsAsId: str, subscriptionId: str, data: Request):
    start_time = time()
    try:
        data_dict = await data.json()
        mon_evt_sub = MonitoringEventSubscription.from_dict(data_dict)
        await monitoringEventSubscription.monitoring_event_subscriptionscription_update(scsAsId, subscriptionId, mon_evt_sub.to_dict())
    except Exception as e:
        raise HTTPException(status_code=httpx.codes.INTERNAL_SERVER_ERROR, detail=e.__str__) # 'Failed to update subscription'
    end_time = (time() - start_time) * 1000
    headers = conf.GLOBAL_HEADERS
    headers.update({'X-ElapsedTime-Header': str(end_time)})
    return Response(status_code=httpx.codes.OK, headers=headers, content="The subscription was updated successfully.")

@app.patch("/3gpp-monitoring-event/v1/{scsAsId}/subscriptions/{subscriptionId}")
async def mon_evt_sub_patch(scsAsId: str, subscriptionId: str, data: Request):
    start_time = time()
    try:
        data_dict = await data.json()
        mon_evt_sub = MonitoringEventSubscription.from_dict(data_dict)

        if not (mon_evt_sub.excluded_external_ids and mon_evt_sub.excluded_msisdns and mon_evt_sub.added_external_ids and mon_evt_sub.added_msisdns):
            raise HTTPException(status_code=httpx.codes.BAD_REQUEST, detail='At least one of "excludedExternalIds", "excludedMsisdns", "addedExternalIds" and/or "addedMsisdns"')
    
        await monitoringEventSubscription.monitoring_event_subscriptionscription_update(scsAsId, subscriptionId, mon_evt_sub.to_dict())
    except Exception as e:
        raise HTTPException(status_code=httpx.codes.INTERNAL_SERVER_ERROR, detail=e.__str__) # 'Failed to update subscription'
    end_time = (time() - start_time) * 1000
    headers = conf.GLOBAL_HEADERS
    headers.update({'X-ElapsedTime-Header': str(end_time)})
    return Response(status_code=httpx.codes.OK, headers=headers, content="The subscription was updated successfully.")

@app.delete("/3gpp-monitoring-event/v1/{scsAsId}/subscriptions/{subscriptionId}")
async def mon_evt_sub_delete(scsAsId: str, subscriptionId: str):
    start_time = time()
    conf.logger.info(f"Initiating {scsAsId} Monitoring Event subscription deletion {subscriptionId}")
    try:
        res = await monitoringEventSubscription.monitoring_event_subscriptionscription_get(scsAsId, subscriptionId)
        if not res:
            raise HTTPException(status_code=httpx.codes.NOT_FOUND, detail="Subscription not found!")
        else:
            location = res['location']
            async with httpx.AsyncClient(http1=True if conf.CORE=="free5gc" else False, http2=None if conf.CORE=="free5gc" else True) as client:
                res = await client.delete(
                    location,
                    headers={'Accept': 'application/json,application/problem+json'},
                )
                conf.logger.info(f"Response {res.status_code} for deleting app session. Content:")
                conf.logger.info(res.text)
            if res.status_code != httpx.codes.NO_CONTENT:
                conf.logger.info("Context not found!")
                raise HTTPException(status_code=httpx.codes.NOT_FOUND, detail="Subscription not found!")
            res = await monitoringEventSubscription.monitoring_event_subscriptionscription_delete(scsAsId, subscriptionId)
            if res == 1:
                end_time = (time() - start_time) * 1000
                headers = conf.GLOBAL_HEADERS
                headers.update({'X-ElapsedTime-Header': str(end_time)})
                return Response(status_code=httpx.codes.NO_CONTENT, headers=headers)
    except Exception as e:
        raise HTTPException(status_code=httpx.codes.INTERNAL_SERVER_ERROR, detail=e.__str__)

#---------------------traffic-influence------------------------
@app.get("/tiget")
async def tiget():
    conf.logger.info("getting all subscription")
    res = await trafficInfluSub.get()
    if not res:
        return {'subs': []}
    return {'subs': res}

@app.get("/tiget/{subId}")
async def tiget(subid: str=None):
    if not subid:
        raise HTTPException(status_code=httpx.codes.BAD_REQUEST, detail="Subscription ID not provided!")
    conf.logger.info(f"getting subscription: {subid}")
    res = await trafficInfluSub.get(subId=subid)
    if not res:
        return {'subs': []}
    return {'subs': res}

@app.get("/tidelete/{subId}")
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

@app.get("/3gpp-traffic-influence/v1/{afId}/subscriptions/{subId}")
async def ti_get(afId: str, subId: str=None):
    start_time = time()
    conf.logger.info(f"Initiating {afId} Traffic Influence subscription retrieval {subId}")
    res = await trafficInfluSub.traffic_influence_subscription_get(afId, subId)
    if not res:
        raise HTTPException(status_code=httpx.codes.NOT_FOUND, detail="content not found")
    end_time = (time() - start_time) * 1000
    headers = conf.GLOBAL_HEADERS
    headers.update({'X-ElapsedTime-Header': str(end_time)})
    return Response(content=json.dumps(res), headers=headers, status_code=httpx.codes.OK)

@app.get("/3gpp-traffic-influence/v1/{afId}/subscriptions")
async def ti_get_all(afId: str):
    start_time = time()
    conf.logger.info(f"Initiating {afId} Traffic Influence subscriptions retrieval")
    res = await trafficInfluSub.traffic_influence_subscription_get(afId)
    if not res:
        raise HTTPException(status_code=httpx.codes.NOT_FOUND, detail="content not found")
    end_time = (time() - start_time) * 1000
    headers = conf.GLOBAL_HEADERS
    headers.update({'X-ElapsedTime-Header': str(end_time)})
    return Response(content=json.dumps(res), headers=headers, status_code=httpx.codes.OK)

@app.post("/3gpp-traffic-influence/v1/{afId}/subscriptions")
async def traffic_influ_create(afId: str, data: Request, background_tasks: BackgroundTasks):
    start_time = time()
    conf.logger.info(f"Initiating {afId} Traffic Influence subscription creation")
    try:
        data_dict = await data.json()
        traffic_sub = TrafficInfluSub.from_dict(data_dict)
    except ValueError as e:
        raise HTTPException(status_code=httpx.codes.BAD_REQUEST, detail=f"Failed to parse message. Err: {e.__str__}")
    except Exception as e:
        raise HTTPException(status_code=httpx.codes.INTERNAL_SERVER_ERROR, detail=e.__str__)

    if not ((traffic_sub.af_app_id is not None)^(traffic_sub.traffic_filters is not None)^(traffic_sub.eth_traffic_filters is not None)):
        conf.logger.info(f"app id: {type(traffic_sub.af_app_id)}, traffic filters: {type(traffic_sub.traffic_filters)}, eth traffic filters: {type(traffic_sub.eth_traffic_filters)}")
        raise HTTPException(httpx.codes.BAD_REQUEST, detail="Only one of afAppId, trafficFilters or ethTrafficFilters")
    if not ((traffic_sub.ipv4_addr is not None)^(traffic_sub.ipv6_addr is not None)^(traffic_sub.mac_addr is not None)^(traffic_sub.gpsi is not None)^(traffic_sub.external_group_id is not None)^(traffic_sub.any_ue_ind is not None)):
        conf.logger.info(f"ipv4: {type(traffic_sub.ipv4_addr)}, any ue: {type(traffic_sub.any_ue_ind)}")
        raise HTTPException(httpx.codes.BAD_REQUEST, detail="Only one of ipv4Addr, ipv6Addr, macAddr, gpsi, externalGroupId or anyUeInd")
   
    #---------------------------any ue, gpsi or ext group id------------------------
    if traffic_sub.any_ue_ind or traffic_sub.gpsi or traffic_sub.external_group_id:
        if traffic_sub.any_ue_ind and not traffic_sub.dnn or not traffic_sub.snssai:
            raise HTTPException(httpx.codes.BAD_REQUEST, detail="Cannot parse message")
        supi = intGroupId = None
        if traffic_sub.gpsi:
            supi = udm_handler.udm_sdm_id_translation(traffic_sub.gpsi)
        elif traffic_sub.external_group_id:
            intGroupId = udm_handler.udm_sdm_group_identifiers_translation(traffic_sub.external_group_id)
        res = await udr_handler.udr_app_data_insert(traffic_sub, intGroupId, supi)
        if res.status_code == httpx.codes.CREATED:
            sub_id = trafficInfluSub.traffic_influence_subscription_insert(afId, traffic_sub, res.headers['location'])
            if sub_id:
                traffic_sub.__self = f"http://{conf.HOSTS['NEF'][0]}/3gpp-traffic-influence/v1/{afId}/subscriptions/{sub_id}"
                traffic_sub.supp_feat = "ffff"
                headers={'location': traffic_sub.__self, 'content-type': 'application/json'}
                if traffic_sub.request_test_notification:
                    test_notif = EventNotification(af_trans_id=traffic_sub.af_trans_id)
                    background_tasks.add_task(send_notification, test_notif.to_dict(), traffic_sub.notification_destination)
                end_time = (time() - start_time) * 1000
                headers = conf.GLOBAL_HEADERS
                headers.update({'X-ElapsedTime-Header': str(end_time)})
                return JSONResponse(status_code=httpx.codes.CREATED, content=traffic_sub.to_dict(), headers=headers)
            else:
                conf.logger.info("Server error")
                raise HTTPException(status_code=500, detail="Error creating resource")
        else:
            raise HTTPException(status_code=500, detail="Error creating resource")
        
    #------------------------ipv4, ipv6 or eth---------------------------
    else:
        if "BSF" in conf.HOSTS.keys():
            bsf_params = {}
            bsf_params['gpsi'] = traffic_sub.gpsi
            bsf_params['dnn'] = traffic_sub.dnn,
            bsf_params['snssai'] = traffic_sub.snssai
            if traffic_sub.ipv4_addr:
                bsf_params['ipv4Addr'] = traffic_sub.ipv4_addr
            elif traffic_sub.ipv6_addr:
                bsf_params['ipv6Prefix'] = traffic_sub.ipv6_addr
            elif traffic_sub.mac_addr:
                bsf_params['macAddr48'] = traffic_sub.mac_addr

            res = await bsf_handler.bsf_management_discovery(bsf_params)
            if res['code'] != httpx.codes.OK:
                raise HTTPException(status_code=httpx.codes.NOT_FOUND, detail="Session not found")
            
            pcf_binding = PcfBinding.from_dict(res['response'])
            _id = str(uuid.uuid4().hex)
            while await trafficInfluSub.check_id(_id):
                _id = str(uuid.uuid4().hex)
            res = await pcf_handler.pcf_policy_authorization_create_ti(pcf_binding, traffic_sub, _id)
        else:
            _id = str(uuid.uuid4().hex)
            while await trafficInfluSub.check_id(_id):
                _id = str(uuid.uuid4().hex)
            res = await pcf_handler.pcf_policy_authorization_create_ti(traffic_influ_sub=traffic_sub, _id=_id)

        if res.status_code == httpx.codes.CREATED:
            conf.logger.info("Storing request and generating 'Traffic Influence' resource.")
            sub_id = await trafficInfluSub.traffic_influence_subscription_insert(afId, traffic_sub, res.headers['location'], _id)
            if sub_id:
                if traffic_sub.request_test_notification:
                    test_notif = {'subscription': traffic_sub.notification_destination}
                    background_tasks.add_task(send_notification, test_notif, traffic_sub.notification_destination)
                traffic_sub.__self = f"http://{conf.HOSTS['NEF'][0]}/3gpp-traffic-influence/v1/{afId}/subscriptions/{sub_id}"
                conf.logger.info(f"Resource stored at {traffic_sub.__self} with ID: {sub_id}")
                headers = conf.GLOBAL_HEADERS
                headers['location'] = traffic_sub.__self
                end_time = (time() - start_time) * 1000
                headers = conf.GLOBAL_HEADERS
                headers.update({'X-ElapsedTime-Header': str(end_time)})
                return JSONResponse(status_code=httpx.codes.CREATED, content=traffic_sub.to_dict(), headers=headers)
            else:
                conf.logger.info("Server error")
                return Response(status_code=httpx.codes.INTERNAL_SERVER_ERROR, content="Error creating resource!")
    return Response(status_code=httpx.codes.INTERNAL_SERVER_ERROR, content="Unknown server error!")

@app.put("/3gpp-traffic-influence/v1/{afId}/subscriptions/{subId}")
async def ti_put(afId: str, subId: str, data: Request):
    start_time = time()
    try:
        data_dict = await data.json()
        traffic_sub = TrafficInfluSub.from_dict(data_dict)
        res = await trafficInfluSub.individual_traffic_influence_subscription_update(afId=afId, subId=subId, sub=traffic_sub.to_dict())
    except Exception as e:
        raise HTTPException(status_code=httpx.codes.INTERNAL_SERVER_ERROR, detail=e.__str__)
    end_time = (time() - start_time) * 1000
    headers = conf.GLOBAL_HEADERS
    headers.update({'X-ElapsedTime-Header': str(end_time)})
    return Response(status_code=httpx.codes.OK, headers=headers, content=res)

@app.patch("/3gpp-traffic-influence/v1/{afId}/subscriptions/{subId}")
async def ti_patch(afId: str, subId: str, data: Request):
    start_time = time()
    try:
        traffic_sub = TrafficInfluSubPatch.from_dict(data.json())
        res = await trafficInfluSub.individual_traffic_influence_subscription_update(afId=afId, subId=subId, sub=traffic_sub.to_dict(), partial=True)
    except Exception as e:
        raise HTTPException(status_code=httpx.codes.INTERNAL_SERVER_ERROR, detail=e.__str__)
    end_time = (time() - start_time) * 1000
    headers = conf.GLOBAL_HEADERS
    headers.update({'X-ElapsedTime-Header': str(end_time)})
    return Response(status_code=httpx.codes.OK, headers=headers, content=res)

@app.delete("/3gpp-traffic-influence/v1/{afId}/subscriptions/{subId}")
async def delete_ti(afId: str, subId: str):
    start_time = time()
    conf.logger.info(f"Initiating {afId} Traffic Influence subscription deletion: {subId}")
    try:
        res = await trafficInfluSub.traffic_influence_subscription_get(afId, subId)
        if not res:
            raise HTTPException(status_code=httpx.codes.NOT_FOUND, detail="Subscription not found!")
        else:
            contextId = res['location'].split('/')[-1]
            res = await pcf_handler.pcf_policy_authorization_delete(contextId)
            if res.status_code != httpx.codes.NO_CONTENT:
                conf.logger.info("Context not found!")
                raise HTTPException(status_code=httpx.codes.NOT_FOUND, detail="Subscription not found!")

            conf.logger.info(f"deleting: {subId} from db")
            res = await trafficInfluSub.individual_traffic_influence_subscription_delete(afId, subId)
            if res == 1:
                end_time = (time() - start_time) * 1000
                headers = conf.GLOBAL_HEADERS
                headers.update({'X-ElapsedTime-Header': str(end_time)})
                return Response(status_code=httpx.codes.NO_CONTENT, headers=headers)
    except Exception as e:
        raise HTTPException(status_code=httpx.codes.INTERNAL_SERVER_ERROR, detail=e.__str__)



#---------------------as-session-with-qos------------------------
@app.get("/qget")
async def qget():
    conf.logger.info("getting all subscription")
    res = await asSessionWithQoSSub.get()
    if not res:
        return {'subs': []}
    return {'subs': res}

@app.get("/qget/{subId}")
async def qget(subId: str=None):
    if not subId:
        raise HTTPException(status_code=httpx.codes.BAD_REQUEST, detail="Subscription ID not provided!")
    conf.logger.info(f"getting subscription: {subId}")
    res = await asSessionWithQoSSub.get(subId)
    if not res:
        return {'subs': []}
    return {'subs': res}

@app.get("/qdelete/{subId}")
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

@app.get("/3gpp-as-session-with-qos/v1/{scsAsId}/subscriptions/{subId}")
async def qos_get(scsAsId: str, subId: str):
    start_time = time()
    conf.logger.info(f"Initiating {scsAsId} AS Session With QoS subscription retrieve {subId}")
    res = await asSessionWithQoSSub.as_session_with_qos_subscription_get(scsAsId, subId)
    if not res:
        raise HTTPException(status_code=httpx.codes.NOT_FOUND, detail="content not found")
    end_time = (time() - start_time) * 1000
    headers = conf.GLOBAL_HEADERS
    headers.update({'X-ElapsedTime-Header': str(end_time)})
    return Response(content=json.dumps(res), headers=headers, status_code=httpx.codes.OK)

@app.get("/3gpp-as-session-with-qos/v1/{scsAsId}/subscriptions")
async def qos_get_all(scsAsId: str):
    start_time = time()
    conf.logger.info(f"Initiating {scsAsId} AS Session With QoS subscriptions retrieve")
    res = await asSessionWithQoSSub.as_session_with_qos_subscription_get(scsAsId)
    if not res:
        raise HTTPException(status_code=httpx.codes.NOT_FOUND, detail="content not found")
    end_time = (time() - start_time) * 1000
    headers = conf.GLOBAL_HEADERS
    headers.update({'X-ElapsedTime-Header': str(end_time)})
    return Response(content=json.dumps(res), headers=headers, status_code=httpx.codes.OK)

@app.post("/3gpp-as-session-with-qos/v1/{scsAsId}/subscriptions")
async def qos_create(scsAsId: str, data: Request, background_tasks: BackgroundTasks):
    start_time = time()
    conf.logger.info(f"Initiating {scsAsId} AS Session With QoS subscription creation")

    try:
        data_dict = await data.json()
        qos_sub = AsSessionWithQoSSubscription().from_dict(data_dict)
    except ValueError as e:
        raise HTTPException(status_code=httpx.codes.BAD_REQUEST, detail=f"Failed to parse message. Err: {e.__str__}")
    except Exception as e:
        raise HTTPException(status_code=httpx.codes.INTERNAL_SERVER_ERROR, detail=e.__str__)

    if not ((qos_sub.ue_ipv4_addr is not None)^(qos_sub.ue_ipv6_addr is not None)^(qos_sub.mac_addr is not None)):
        conf.logger.info("Only one of ipv4Addr, ipv6Addr or macAddr")
        raise HTTPException(httpx.codes.BAD_REQUEST, detail="Only one of ipv4Addr, ipv6Addr or macAddr")
    if not ((qos_sub.flow_info is not None)^(qos_sub.eth_flow_info is not None)^(qos_sub.exter_app_id is not None)):
        conf.logger.info("Only one of IP flow info, Ethernet flow info or External Application")
        raise HTTPException(httpx.codes.BAD_REQUEST, detail="Only one of IP flow info, Ethernet flow info or External Application")
    if (qos_sub.ue_ipv4_addr or qos_sub.ue_ipv6_addr) and not qos_sub.flow_info:
        conf.logger.info("No flow info")
        raise HTTPException(httpx.codes.BAD_REQUEST, detail="cannot parse message")
    if qos_sub.mac_addr and not qos_sub.eth_flow_info:
        conf.logger.info("No eth flow info")
        raise HTTPException(httpx.codes.BAD_REQUEST, detail="cannot parse message")
    if (qos_sub.qos_reference and qos_sub.alt_qos_reqs) or (qos_sub.alt_qo_s_references and qos_sub.alt_qos_reqs):
        conf.logger.info("Alt QoS Ref & Alt QoS Reqs are mutually exclusive. If qos reference alt qos reqs should not be provided")
        raise HTTPException(httpx.codes.BAD_REQUEST, detail="cannot parse message")
    if qos_sub.qos_mon_info and "QOS_MONITORING" not in qos_sub.events:
        conf.logger.info("qos mon info and events and QOS_MONITORING not in events")
        raise HTTPException(httpx.codes.BAD_REQUEST, detail="cannot parse message")
    if qos_sub.alt_qo_s_references and not qos_sub.notification_destination:
        conf.logger.info("no notif destination")
        raise HTTPException(httpx.codes.BAD_REQUEST, detail="cannot parse message")
    
    conf.logger.info("\n------------------------------qos sub---------------------------------------")
    conf.logger.info(qos_sub.to_str())
    conf.logger.info("---------------------------------------------------------------------\n")
    if "BSF" in conf.HOSTS.keys():
        bsf_params = {}
        if qos_sub.ue_ipv4_addr:
            bsf_params['ipv4Addr'] = qos_sub.ue_ipv4_addr
        elif qos_sub.ue_ipv6_addr:
            bsf_params['ipv6Prefix'] = qos_sub.ue_ipv6_addr
        elif qos_sub.mac_addr:
            bsf_params['macAddr48'] = qos_sub.mac_addr

        res = await bsf_handler.bsf_management_discovery(bsf_params)
        if res['code'] != httpx.codes.OK:
            raise HTTPException(status_code=httpx.codes.NOT_FOUND, detail="Session not found")
        pcf_binding = PcfBinding.from_dict(res['response'])
        _id = str(uuid.uuid4().hex)
        while await asSessionWithQoSSub.check_id(_id):
            _id = str(uuid.uuid4().hex)
        response = await pcf_handler.pcf_policy_authorization_create_qos(pcf_binding, qos_sub, _id)
    else:
        _id = str(uuid.uuid4().hex)
        while await asSessionWithQoSSub.check_id(_id):
            _id = str(uuid.uuid4().hex)
        response = await pcf_handler.pcf_policy_authorization_create_qos(as_session_qos_sub=qos_sub, _id=_id)
    
    if response.status_code == httpx.codes.CREATED:
        conf.logger.info("Storing request and generating 'As Aession With QoS' resource.")
        sub_id = await asSessionWithQoSSub.as_session_with_qos_subscription_insert(scsAsId, qos_sub, response.headers['Location'], _id)
        if sub_id:
            if qos_sub.request_test_notification:
                test_notif = {'subscription': qos_sub.notification_destination}
                background_tasks.add_task(send_notification, test_notif, qos_sub.notification_destination)
            qos_sub.__self = f"http://{conf.HOSTS['NEF'][0]}/3gpp-as-session-with-qos/v1/{scsAsId}/subscriptions/{sub_id}"
            conf.logger.info(f"Resource stored at {qos_sub.__self} with ID: {sub_id}")
            headers = conf.GLOBAL_HEADERS
            headers['location'] = qos_sub.__self
            end_time = (time() - start_time) * 1000
            headers = conf.GLOBAL_HEADERS
            headers.update({'X-ElapsedTime-Header': str(end_time)})
            return JSONResponse(status_code=httpx.codes.CREATED, content=qos_sub.to_dict())
        else:
            conf.logger.info("Error creating resource")
            #delete from pcf
            return Response(status_code=httpx.codes.INTERNAL_SERVER_ERROR, content="Error creating resource!")
    return Response(status_code=response.status_code, content=response.content)

@app.put("/3gpp-as-session-with-qos/v1/{scsAsId}/subscriptions/{subId}")
async def qos_put(scsAsId: str, subId: str, data: Request):
    start_time = time()
    try:
        qosSub = AsSessionWithQoSSubscription.from_dict(data.json())
        await asSessionWithQoSSub.as_session_with_qos_subscription_update(scsAsId=scsAsId, subId=subId, sub=qosSub.to_dict())
    except Exception as e:
        raise HTTPException(status_code=httpx.codes.INTERNAL_SERVER_ERROR, detail=e.__str__)
    end_time = (time() - start_time) * 1000
    headers = conf.GLOBAL_HEADERS
    headers.update({'X-ElapsedTime-Header': str(end_time)})
    return Response(status_code=httpx.codes.OK, headers=headers, content="The subscription was updated successfully.")

@app.patch("/3gpp-as-session-with-qos/v1/{scsAsId}/subscriptions/{subId}")
async def qos_patch(scAsId: str, subId: str, data: Request):
    start_time = time()
    try:
        qosSub = AsSessionWithQoSSubscription.from_dict(data.json())
        await asSessionWithQoSSub.as_session_with_qos_subscription_update(scsAsId=scAsId, subId=subId, sub=qosSub.to_dict(), partial=True)
    except Exception as e:
        raise HTTPException(status_code=httpx.codes.INTERNAL_SERVER_ERROR, detail=e.__str__)
    end_time = (time() - start_time) * 1000
    headers = conf.GLOBAL_HEADERS
    headers.update({'X-ElapsedTime-Header': str(end_time)})
    return Response(status_code=httpx.codes.OK, headers=headers, content="The subscription was updated successfully.")
    
@app.delete("/3gpp-as-session-with-qos/v1/{scsAsId}/subscriptions/{subId}")
async def qos_delete(scsAsId: str, subId: str):
    start_time = time()
    conf.logger.info(f"Initiating {scsAsId} AS Session With QoS subscription deletion: {subId}")
    res = await asSessionWithQoSSub.as_session_with_qos_subscription_get(scsAsId, subId)
    if not res:
        raise HTTPException(status_code=httpx.codes.NOT_FOUND, detail="Subscription not found!")
    else:
        contextId = res['location'].split('/')[-1]
        res = await pcf_handler.pcf_policy_authorization_delete(contextId)
        if res.status_code != httpx.codes.NO_CONTENT:
            conf.logger.info("Context not found!")
            raise HTTPException(status_code=httpx.codes.NOT_FOUND, detail="Subscription not found!")
        
        conf.logger.info(f"deleting: {subId} from db")
        res = await asSessionWithQoSSub.as_session_with_qos_subscription_delete(scsAsId, subId)
        if res == 1:
            end_time = (time() - start_time) * 1000
            headers = conf.GLOBAL_HEADERS
            headers.update({'X-ElapsedTime-Header': str(end_time)})
            return Response(status_code=httpx.codes.NO_CONTENT, headers=headers)
    raise HTTPException(status_code=httpx.codes.INTERNAL_SERVER_ERROR, detail="Failed to delete subscription")

#
#
@app.get("/clean")
async def clean():
    res = clean_db()
    if res:
        return {"result": "Database cleaned."}
    else:
        raise HTTPException(status_code=httpx.codes.INTERNAL_SERVER_ERROR, detail="Error cleaning database!")
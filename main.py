import json
import httpx
from fastapi import APIRouter, FastAPI, Request, Response, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.routing import APIRoute
from fastapi_utils.tasks import repeat_every
from typing import Callable, Coroutine
from session import clean_db
from api.config import conf
from models.pcf_binding import PcfBinding
from models.monitoring_event_subscription import MonitoringEventSubscription
from models.monitoring_event_report import MonitoringEventReport
from models.monitoring_event_reports import MonitoringEventReports
from models.traffic_influ_sub import TrafficInfluSub
from models.traffic_influ_sub_patch import TrafficInfluSubPatch
from models.event_notification import EventNotification
from models.as_session_with_qo_s_subscription import AsSessionWithQoSSubscription
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

class CustomRouter(APIRoute):
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_andler()
        
        async def custom_route_handler(request: Response) -> Response:
            try:
                response: Response = await original_route_handler(response)
            except RequestValidationError as exc:
                body = await request.body()
                detail = {"errors": exc.errors(), "body": body.decode()}
                raise HTTPException(status_code=500, detail=detail)

        return custom_route_handler

app = FastAPI(debug=True)
# router = APIRouter(route_class=CustomRouter)

@app.exception_handler(Exception)
async def exception_callback(request: Request, exc: Exception):
    conf.logger.info(f"Failed method {request.method} at URL {request.url}.")
    conf.logger.info(f"Exception message is {exc!r}.")

# @app.middleware('http')
# async def req_middleware(request: Request, call_next):
#     try:
#         response = await call_next(request)
#         conf.logger.info(f"INFO - {request.method}: {request.url}")
#         if request.method in ["POST", "PUT", "PATCH"]:
#             body = await request.body()
#             conf.logger.info(f"body: {body}")
#     except RequestValidationError as exc:
#         conf.logger.error(f"ERROR - {request.method}: {request.url}")
#     return response

@app.on_event("startup")
async def startup():
    try:
        conf.logger.info("Registering NEF...")
        res = await nrf_handler.nf_register()
        if res.status_code == httpx.codes.CREATED:
            await nrf_heartbeat()
        conf.logger.info("NF discovery...")
        await nrf_handler.nrf_discovery()
        conf.logger.info("NF status subscribe...")
        await status_subscribe()
        conf.logger.info("amf UE event subscription")
        await amf_handler.amf_event_exposure_subscribe()
        conf.logger.info("udm UE event subscription")
        await udm_handler.udm_ee_subscription_create()
    except Exception as e:
        conf.logger.info(f"Error starting up: {e}")
    # TLS dependant
    # conf.logger.info("Getting access token...")
    # res = await nrf_handler.nrf_get_access_token()


@repeat_every(seconds=conf.NEF_PROFILE.heart_beat_timer - 2)
async def nrf_heartbeat():
    await nrf_handler.nf_register_heart_beat()

@repeat_every(seconds=86400)
async def status_subscribe():
    try:
        await nrf_handler.nf_status_subscribe(list(conf.NF_SCOPES.keys()))
    except Exception as e:
        conf.logger.error(e)

@app.on_event("shutdown")
async def shutdown():
    conf.logger.info("shuting down...")
    await nrf_handler.nf_deregister()
    await nrf_handler.nf_status_unsubscribe()
    # clean_db()

@app.get("/")
async def read_root():
    insts = await nfProfile.get_all()
    return {'nfs instances': str(insts)}

async def send_notification(data: str, link: str):
    async with httpx.AsyncClient(http1=True if conf.CORE=="free5gc" else False, http2=None if conf.CORE=="free5gc" else True) as client:
        response = await client.post(
            link,
            headers=conf.GLOBAL_HEADERS,
            data=json.dumps(data)
        )
        conf.logger.info(response.text)

@app.get("/ue/{supi}")
async def ue_info(supi: str):
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

@app.get("/{ueid}/translate")
async def translate_id(ueid: str):
    translated_id = await udm_handler.udm_sdm_id_translation(ueid)
    conf.logger.info(f"translated id: {translated_id}")
    return translated_id

#-----------------------------callback endpoints---------------------------------
@app.post("/nnef-callback/amf-event-sub-callback")
async def amf_evt_sub_callback(request: Request):
    conf.logger.info(request.method)
    conf.logger.info(request.body)

@app.post("/nnef-callback/udm-event-sub-callback")
async def udm_evt_sub_callback(request: Request):
    conf.logger.info(request.method)
    conf.logger.info(request.body)
    mon_evt_rep = MonitoringEventReport()
    return Response(status_code=httpx.codes.OK, headers=conf.GLOBAL_HEADERS, content={
        # 'MonitoringEventSubscription': mon_evt_sub.to_dict(),
        'MonitoringEventReport': mon_evt_rep.to_dict()
    })

@app.post("/nnrf-nfm/v1/subscriptions")
async def nrf_notif(request: Request):
    conf.logger.info(request.method)
    conf.logger.info(request.body)

@app.put("/up_path_change")
async def up_path_chg_notif(request: Request):
    conf.logger.info(request.method)
    conf.logger.info(request.text)
    try:
        data = await request.json()
    except Exception as e:
        conf.logger.info(f"{e!r}")
    evt_notif = EventNotification()
    if data:
        conf.logger.info(data)
    return Response(status_code=httpx.codes.NO_CONTENT)

@app.post("/up_path_change")
async def up_path_chg_notif(request: Request):
    conf.logger.info(request.method)
    conf.logger.info(request.text)
    try:
        data = await request.json()
    except Exception as e:
        conf.logger.info(f"{e!r}")
    evt_notif = EventNotification()
    if data:
        conf.logger.info(data)
    return Response(status_code=httpx.codes.NO_CONTENT)

#---------------------monitoring-event------------------------
@app.get("/monget")
async def mon_get():
    res = await monitoringEventSubscription.monitoring_event_subscriptionscription_get()
    if not res:
        return {'subs': []}
    return {'subs': res}

@app.get("/mondelete/{subId}")
async def mon_del(subId: str):
    try:
        res = await monitoringEventSubscription.monitoring_event_subscriptionscription_get(subId)
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
            res = await monitoringEventSubscription.monitoring_event_subscriptionscription_delete(subId)
            if res == 1:
                return Response(status_code=httpx.codes.NO_CONTENT)
    except Exception as e:
        raise HTTPException(status_code=httpx.codes.INTERNAL_SERVER_ERROR, detail=e.__str__)


@app.get("/3gpp-monitoring-event/v1/{scsAsId}/subscriptions/{subscriptionId}")
async def mon_evt_subs_get(scsAsId: str, subscriptionId: str):
    conf.logger.info(f"af id: {scsAsId}, subscription id: {subscriptionId}")
    res = await monitoringEventSubscription.monitoring_event_subscriptionscription_get(scsAsId, subscriptionId)
    if not res:
        raise HTTPException(status_code=httpx.codes.NOT_FOUND, detail="content not found")
    return Response(content=res, status_code=httpx.codes.OK)

@app.get("/3gpp-monitoring-event/v1/{scsAsId}/subscriptions")
async def mon_evt_subs_get_all(scsAsId: str):
    conf.logger.info(f"af id: {scsAsId}")
    res = await monitoringEventSubscription.monitoring_event_subscriptionscription_get(scsAsId)
    if not res:
        raise HTTPException(status_code=httpx.codes.NOT_FOUND, detail="content not found")
    return Response(content=res, status_code=httpx.codes.OK)

@app.post("/3gpp-monitoring-event/v1/{scsAsId}/subscriptions")
async def mon_evt_subs_post(scsAsId: str, data: Request):
    try:
        data_dict = await data.json()
        mon_evt_sub = MonitoringEventSubscription.from_dict(data_dict)
    except ValueError as e:
        raise HTTPException(status_code=httpx.codes.BAD_REQUEST, detail=f"Failed to parse message. Err: {e.__str__}")
    except Exception as e:
        raise HTTPException(status_code=httpx.codes.INTERNAL_SERVER_ERROR, detail=e.__str__)

    if not mon_evt_sub.supported_features:
        raise HTTPException(status_code=httpx.codes.BAD_REQUEST, detail=f"EVENT_FEATURE_MISMATCH. Supported features are {conf.SERVICE_LIST['nnef-evt']}")
    
    if hex(int(mon_evt_sub.supported_features, 16)) and hex(int(conf.SERVICE_LIST['nnef-evt'], 16)) == hex(0):
        raise HTTPException(status_code=httpx.codes.INTERNAL_SERVER_ERROR, detail=f"EVENT_UNSUPPORTED. Supported features are {conf.SERVICE_LIST['nnef-evt']}")
    
    if mon_evt_sub.location_type or mon_evt_sub.accuracy or mon_evt_sub.minimum_report_interval:
        if not ((mon_evt_sub.external_id is not None)^(mon_evt_sub.msisdn is not None)^(mon_evt_sub.ipv4_addr is not None)^(mon_evt_sub.ipv6_addr is not None)^(mon_evt_sub.external_group_id is not None)):
            raise HTTPException(httpx.codes.BAD_REQUEST, detail='One of the properties "externalId", "msisdn", "ipv4Addr", "ipv6Addr" or "externalGroupId" shall be included for features "Location_notification" and "Communication_failure_notification"')
    
    if mon_evt_sub.location_type or mon_evt_sub.accuracy or mon_evt_sub.minimum_report_interval or mon_evt_sub.max_rpt_expire_intvl or mon_evt_sub.sampling_interval or mon_evt_sub.reporting_loc_est_ind or mon_evt_sub.linear_distance or mon_evt_sub.loc_qo_s or mon_evt_sub.svc_id or mon_evt_sub.ldr_type or mon_evt_sub.velocity_requested or mon_evt_sub.max_age_of_loc_est or mon_evt_sub.loc_time_window or mon_evt_sub.supported_gad_shapes or mon_evt_sub.code_word or mon_evt_sub.location_area5_g:
        if not ((mon_evt_sub.external_id is not None)^(mon_evt_sub.msisdn is not None)^(mon_evt_sub.external_group_id is not None)):
            raise HTTPException(httpx.codes.BAD_REQUEST, detail='One of the properties "externalId", "msisdn" or "externalGroupId" shall be included for feature "eLCS"')
        
    if not mon_evt_sub.monitoring_type or mon_evt_sub.notification_destination:
        raise HTTPException(status_code=httpx.codes.BAD_REQUEST, detail='Message shall include SCS/AS Identifier, "Monitoring Type", "Notification Destination Address" and pne of External Identifier, MSISDN or External Group Identifier')

    if mon_evt_sub.maximum_number_of_reports == 1 and mon_evt_sub.monitor_expire_time:
        raise HTTPException(status_code=httpx.codes.BAD_REQUEST, detail='Cannot parse message.')
    
    if (mon_evt_sub.reachability_type == "SMS" and mon_evt_sub.monitoring_type == "UE_REACHABILITY") or (mon_evt_sub.location_type == "LAST_KNOWN_LOCATION" and mon_evt_sub.monitoring_type == "LOCATION_REPORTING"):
        if mon_evt_sub.maximum_number_of_reports != 1:
            raise HTTPException(status_code=httpx.codes.BAD_REQUEST, detail='Only one-time reporting supported for this event.')

    if mon_evt_sub.monitoring_type == "NUMBER_OF_UES_IN_AN_AREA" and mon_evt_sub.maximum_number_of_reports != 1:
        raise HTTPException(status_code=httpx.codes.BAD_REQUEST, detail='Only one-time reporting supported for this event.')

    if mon_evt_sub.monitoring_type in ['NUMBER_OF_UES_IN_AN_AREA']:
        res = amf_handler.amf_event_exposure_subscribe()
    elif mon_evt_sub.monitoring_type in ['LOSS_OF_CONNECTIVITY','UE_REACHABILITY','LOCATION_REPORTING','CHANGE_OF_IMSI_IMEI_ASSOCIATION','ROAMING_STATUS','COMMUNICATION_FAILURE','AVAILABILITY_AFTER_DDN_FAILURE','PDN_CONNECTIVITY_STATUS','API_SUPPORT_CAPABILITY']:
        res = udm_handler.udm_ee_subscription_create(mon_evt_sub, scsAsId)

    if res.status_code == httpx.codes.CREATED:
        if mon_evt_sub.maximum_number_of_reports > 1:
            inserted = monitoringEventSubscription.monitoring_event_subscriptionscription_insert(scsAsId, mon_evt_sub, res.headers['location'])
            location = f"http://{conf.HOSTS['NEF'][0]}/3gpp-monitoring-event/v1/{scsAsId}/subscriptions/{res}"
            mon_evt_sub._self = location
            headers = conf.GLOBAL_HEADERS
            headers['location'] = location
            return Response(status_code=httpx.codes.CREATED, headers=headers, content=mon_evt_sub.to_dict())

@app.put("/3gpp-monitoring-event/v1/{scsAsId}/subscriptions/{subscriptionId}")
async def mon_evt_sub_put(scsAsId: str, subscriptionId: str, data: Request):
    try:
        data_dict = await data.json()
        mon_evt_sub = MonitoringEventSubscription.from_dict(data_dict)
        await monitoringEventSubscription.monitoring_event_subscriptionscription_update(scsAsId, subscriptionId, mon_evt_sub.to_dict())
    except Exception as e:
        raise HTTPException(status_code=httpx.codes.INTERNAL_SERVER_ERROR, detail=e.__str__) # 'Failed to update subscription'
    return Response(status_code=httpx.codes.OK, content="The subscription was updated successfully.")

@app.patch("/3gpp-monitoring-event/v1/{scsAsId}/subscriptions/{subscriptionId}")
async def mon_evt_sub_patch(scsAsId: str, subscriptionId: str, data: Request):
    try:
        data_dict = await data.json()
        mon_evt_sub = MonitoringEventSubscription.from_dict(data_dict)

        if not (mon_evt_sub.excluded_external_ids and mon_evt_sub.excluded_msisdns and mon_evt_sub.added_external_ids and mon_evt_sub.added_msisdns):
            raise HTTPException(status_code=httpx.codes.BAD_REQUEST, detail='At least one of "excludedExternalIds", "excludedMsisdns", "addedExternalIds" and/or "addedMsisdns"')
    
        await monitoringEventSubscription.monitoring_event_subscriptionscription_update(scsAsId, subscriptionId, mon_evt_sub.to_dict())
    except Exception as e:
        raise HTTPException(status_code=httpx.codes.INTERNAL_SERVER_ERROR, detail=e.__str__) # 'Failed to update subscription'
    return Response(status_code=httpx.codes.OK, content="The subscription was updated successfully.")

@app.delete("/3gpp-monitoring-event/v1/{scsAsId}/subscriptions/{subscriptionId}")
async def mon_evt_sub_delete(scsAsId: str, subscriptionId: str):
    try:
        res = await monitoringEventSubscription.monitoring_event_subscriptionscription_get(scsAsId, subscriptionId)
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
            res = await monitoringEventSubscription.monitoring_event_subscriptionscription_delete(scsAsId, subscriptionId)
            if res == 1:
                return Response(status_code=httpx.codes.NO_CONTENT)
    except Exception as e:
        raise HTTPException(status_code=httpx.codes.INTERNAL_SERVER_ERROR, detail=e.__str__)

#---------------------traffic-influence------------------------
# @app.get("/3gpp-traffic-influence/v1/{afId}/subscriptions")
@app.get("/tiget")
async def tiget():
    res = await trafficInfluSub.traffic_influence_subscription_get()
    if not res:
        return {'subs': []}
    return {'subs': res}

@app.get("/tidelete/{subId}")
async def tidelete(subId: str):
    scsAsId = "test_AF_1"
    res = await trafficInfluSub.individual_traffic_influence_subscription_delete(scsAsId, subId)
    if not res:
        raise HTTPException(status_code=httpx.codes.NOT_FOUND, detail="Subscription not found!")
    else:
        contextId = res['location'].split('/')[-1]
        res = await pcf_handler.pcf_policy_authorization_delete(contextId)
        if res.status_code != httpx.codes.NO_CONTENT:
            conf.logger.info("Context not found!")

        res = await trafficInfluSub.individual_traffic_influence_subscription_delete(scsAsId, subId)
        if res == 1:
            return Response(status_code=httpx.codes.NO_CONTENT)
    raise HTTPException(status_code=httpx.codes.INTERNAL_SERVER_ERROR, detail="Failed to delete subscription")

@app.get("/3gpp-traffic-influence/v1/{afId}/subscriptions/{subId}")
async def ti_get(afId: str, subId: str):
    conf.logger.info(f"af id: {afId}, sub id: {subId}")
    res = await trafficInfluSub.traffic_influence_subscription_get(afId, subId)
    if not res:
        raise HTTPException(status_code=httpx.codes.NOT_FOUND, detail="content not found")
    return Response(content=json.dumps(res), status_code=httpx.codes.OK)

@app.get("/3gpp-traffic-influence/v1/{afId}/subscriptions")
async def ti_get_all(afId: str):
    res = await trafficInfluSub.traffic_influence_subscription_get(afId)
    if not res:
        raise HTTPException(status_code=httpx.codes.NOT_FOUND, detail="content not found")
    return Response(content=json.dumps(res), status_code=httpx.codes.OK)

@app.post("/3gpp-traffic-influence/v1/{afId}/subscriptions")
async def traffic_influ_create(afId: str, data: Request, background_tasks: BackgroundTasks):
    conf.logger.info("Initiating Traffic Influence request process")

    try:
        data_dict = await data.json()
        traffic_sub = TrafficInfluSub().from_dict(data_dict)
    except ValueError as e:
        raise HTTPException(status_code=httpx.codes.BAD_REQUEST, detail=f"Failed to parse message. Err: {e.__str__}")
    except Exception as e:
        raise HTTPException(status_code=httpx.codes.INTERNAL_SERVER_ERROR, detail=e.__str__)

    if not ((traffic_sub.af_app_id is not None)^(traffic_sub.traffic_filters is not None)^(traffic_sub.eth_traffic_filters is not None)):
        conf.logger.info(f"app id: {type(traffic_sub.af_app_id)}, traffic filters: {type(traffic_sub.traffic_filters)}, eth traffic filters: {type(traffic_sub.eth_traffic_filters)}")
        raise HTTPException(httpx.codes.BAD_REQUEST, detail="Only one of afAppId, trafficFilters or ethTrafficFilters")
    if not ((traffic_sub.ipv4_addr is not None)^(traffic_sub.ipv6_addr is not None)^(traffic_sub.mac_addr is not None)^(traffic_sub.gpsi is not None)^(traffic_sub.external_group_id is not None)^(traffic_sub.any_ue_ind)):
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
                traffic_sub.__self = f"http://{conf.HOSTS['NEF'][0]}/3gpp-trafficInfluence/v1/{afId}/subscriptions/{sub_id}"
                traffic_sub.supp_feat = "0"
                headers={'location': traffic_sub.__self, 'content-type': 'application/json'}
                if traffic_sub.request_test_notification:
                    test_notif = EventNotification(af_trans_id=traffic_sub.af_trans_id)
                    background_tasks.add_task(send_notification, test_notif.to_dict(), traffic_sub.notification_destination)
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
            res = await pcf_handler.pcf_policy_authorization_create_ti(pcf_binding, traffic_sub)
        else:
            res = await pcf_handler.pcf_policy_authorization_create_ti(traffic_influ_sub=traffic_sub)
        
        if res.status_code == httpx.codes.CREATED:
            conf.logger.info("Storing request and generating 'Traffic Influence' resource.")
            sub_id = await trafficInfluSub.traffic_influence_subscription_insert(afId, traffic_sub, res.headers['location'])
            if sub_id:
                if traffic_sub.request_test_notification:
                    test_notif = EventNotification(af_trans_id=traffic_sub.af_trans_id)
                    background_tasks.add_task(send_notification, test_notif.to_dict(), traffic_sub.notification_destination)
                traffic_sub.__self = f"http://{conf.HOSTS['NEF'][0]}/3gpp-traffic-influence/v1/{afId}/subscriptions/{sub_id}"
                conf.logger.info(f"Resource stored at {traffic_sub.__self} with ID: {sub_id}")
                headers = conf.GLOBAL_HEADERS
                headers['location'] = traffic_sub.__self
                return JSONResponse(status_code=httpx.codes.CREATED, content=traffic_sub.to_dict(), headers=headers)
            else:
                conf.logger.info("Server error")
                return Response(status_code=httpx.codes.INTERNAL_SERVER_ERROR, content="Error creating resource!")
    return Response(status_code=httpx.codes.INTERNAL_SERVER_ERROR, content="Unknown server error!")

@app.put("/3gpp-traffic-influence/v1/{afId}/subscriptions/{subId}")
async def ti_put(afId: str, subId: str, data: Request):
    try:
        data_dict = await data.json()
        traffic_sub = TrafficInfluSub.from_dict(data_dict)
        res = await trafficInfluSub.individual_traffic_influence_subscription_update(afId=afId, subId=subId, sub=traffic_sub.to_dict())
    except Exception as e:
        raise HTTPException(status_code=httpx.codes.INTERNAL_SERVER_ERROR, detail=e.__str__)
    return Response(status_code=httpx.codes.OK, content=res)

@app.patch("/3gpp-traffic-influence/v1/{afId}/subscriptions/{subId}")
async def ti_patch(afId: str, subId: str, data: Request):
    try:
        traffic_sub = TrafficInfluSubPatch.from_dict(data.json())
        res = await trafficInfluSub.individual_traffic_influence_subscription_update(afId=afId, subId=subId, sub=traffic_sub.to_dict(), partial=True)
    except Exception as e:
        raise HTTPException(status_code=httpx.codes.INTERNAL_SERVER_ERROR, detail=e.__str__)
    return Response(status_code=httpx.codes.OK, content=res)

@app.delete("/3gpp-trafficInfluence/v1/{afId}/subscriptions/{subId}")
async def delete_ti(afId: str, subId: str):
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

            res = await trafficInfluSub.individual_traffic_influence_subscription_delete(afId, subId)
            if res == 1:
                return Response(status_code=httpx.codes.NO_CONTENT)
    except Exception as e:
        raise HTTPException(status_code=httpx.codes.INTERNAL_SERVER_ERROR, detail=e.__str__)



#---------------------as-session-with-qos------------------------
@app.get("/qget")
async def qget():
    res = await asSessionWithQoSSub.as_session_with_qos_subscription_get()
    if not res:
        return {'subs': []}
    return {'subs': res}

@app.get("/qdelete/{subId}")
async def qo_s_delete(subId: str):
    scsAsId = "test_AF_1"
    res = await asSessionWithQoSSub.as_session_with_qos_subscription_get(scsAsId, subId)
    if not res:
        raise HTTPException(status_code=httpx.codes.NOT_FOUND, detail="Subscription not found!")
    else:
        contextId = res['location'].split('/')[-1]
        res = await pcf_handler.pcf_policy_authorization_delete(contextId)
        if res.status_code != httpx.codes.NO_CONTENT:
            conf.logger.info("Context not found!")

        res = await asSessionWithQoSSub.as_session_with_qos_subscription_delete(scsAsId, subId)
        if res == 1:
            return Response(status_code=httpx.codes.NO_CONTENT)
    raise HTTPException(status_code=httpx.codes.INTERNAL_SERVER_ERROR, detail="Failed to delete subscription")

@app.get("/3gpp-as-session-with-qos/v1/{scsAsId}/subscriptions/{subId}")
async def qos_get(scsAsId: str, subId: str=None):
    res = await asSessionWithQoSSub.as_session_with_qos_subscription_get(scsAsId, subId)
    if not res:
        raise HTTPException(status_code=httpx.codes.NOT_FOUND, detail="content not found")
    return Response(content=json.dumps(res), status_code=httpx.codes.OK)

@app.get("/3gpp-as-session-with-qos/v1/{scsAsId}/subscriptions")
async def qos_get_all(scsAsId: str):
    res = await asSessionWithQoSSub.as_session_with_qos_subscription_get(scsAsId)
    if not res:
        raise HTTPException(status_code=httpx.codes.NOT_FOUND, detail="content not found")
    return Response(content=json.dumps(res), status_code=httpx.codes.OK)

@app.post("/3gpp-as-session-with-qos/v1/{scsAsId}/subscriptions")
async def qos_create(scsAsId: str, data: Request, background_tasks: BackgroundTasks):
    conf.logger.info("\n\n---------------------------------------------------------------------")
    conf.logger.info("Initiating As Session With QoS request process")

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
    if qos_sub.qos_mon_info and qos_sub.events and "QOS_MONITORING" not in qos_sub.events:
        conf.logger.info("qos mon info and events and QOS_MONITORING not in events")
        raise HTTPException(httpx.codes.BAD_REQUEST, detail="cannot parse message")
    if qos_sub.alt_qo_s_references and not qos_sub.notification_destination:
        conf.logger.info("no notif destination")
        raise HTTPException(httpx.codes.BAD_REQUEST, detail="cannot parse message")
    
    conf.logger.info("\n------------------------------qos sub---------------------------------------\n")
    conf.logger.info(qos_sub.to_str())
    conf.logger.info("\n---------------------------------------------------------------------\n")
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
        response = await pcf_handler.pcf_policy_authorization_create_qos(pcf_binding, qos_sub)

    else:
        response = await pcf_handler.pcf_policy_authorization_create_qos(as_session_qos_sub=qos_sub)
    
    if response.status_code == httpx.codes.CREATED:
        conf.logger.info("Storing request and generating 'As Aession With QoS' resource.")
        sub_id = await asSessionWithQoSSub.as_session_with_qos_subscription_insert(scsAsId, qos_sub, response.headers['Location'])
        if sub_id:
            if qos_sub.request_test_notification:
                test_notif = {'subscription': qos_sub.notification_destination}
                background_tasks.add_task(send_notification, test_notif, qos_sub.notification_destination)
            qos_sub.__self = f"http://{conf.HOSTS['NEF'][0]}/3gpp-as-session-with-qos/v1/{scsAsId}/subscriptions/{sub_id}"
            conf.logger.info(f"Resource stored at {qos_sub.__self} with ID: {sub_id}")
            headers = conf.GLOBAL_HEADERS
            headers['location'] = qos_sub.__self
            conf.logger.info("---------------------------------------------------------------------\n\n")
            return JSONResponse(status_code=httpx.codes.CREATED, content=qos_sub.to_dict(), headers=headers)
        else:
            conf.logger.info("---------------------------------------------------------------------\n\n")
            return Response(status_code=httpx.codes.INTERNAL_SERVER_ERROR, content="Error creating resource!")
    conf.logger.info("---------------------------------------------------------------------\n\n")
    return Response(status_code=httpx.codes.INTERNAL_SERVER_ERROR, content="Unknown server error!")

@app.put("/3gpp-as-session-with-qos/v1/{scsAsId}/subscriptions/{subId}")
async def qos_put(scsAsId: str, subId: str, data: Request):
    try:
        qosSub = AsSessionWithQoSSubscription.from_dict(data.json())
        await asSessionWithQoSSub.as_session_with_qos_subscription_update(scsAsId=scsAsId, subId=subId, sub=qosSub.to_dict())
    except Exception as e:
        raise HTTPException(status_code=httpx.codes.INTERNAL_SERVER_ERROR, detail=e.__str__)
    return Response(status_code=httpx.codes.OK, content="The subscription was updated successfully.")

@app.patch("/3gpp-as-session-with-qos/v1/{scsAsId}/subscriptions/{subId}")
async def qos_patch(scAsId: str, subId: str, data: Request):
    try:
        qosSub = AsSessionWithQoSSubscription.from_dict(data.json())
        await asSessionWithQoSSub.as_session_with_qos_subscription_update(scsAsId=scAsId, subId=subId, sub=qosSub.to_dict(), partial=True)
    except Exception as e:
        raise HTTPException(status_code=httpx.codes.INTERNAL_SERVER_ERROR, detail=e.__str__)
    return Response(status_code=httpx.codes.OK, content="The subscription was updated successfully.")
    
@app.delete("/3gpp-as-session-with-qos/v1/{scsAsId}/subscriptions/{subId}")
async def qos_delete(scsAsId: str, subId: str):
    res = await asSessionWithQoSSub.as_session_with_qos_subscription_get(scsAsId, subId)
    if not res:
        raise HTTPException(status_code=httpx.codes.NOT_FOUND, detail="Subscription not found!")
    else:
        contextId = res['location'].split('/')[-1]
        res = await pcf_handler.pcf_policy_authorization_delete(contextId)
        if res.status_code != httpx.codes.NO_CONTENT:
            conf.logger.info("Context not found!")
            raise HTTPException(status_code=httpx.codes.NOT_FOUND, detail="Subscription not found!")
        res = await asSessionWithQoSSub.as_session_with_qos_subscription_delete(scsAsId, subId)
        if res == 1:
            return Response(status_code=httpx.codes.NO_CONTENT)
    raise HTTPException(status_code=httpx.codes.INTERNAL_SERVER_ERROR, detail="Failed to delete subscription")

#----------------------clean db-------------------
#
#
@app.get("/clean")
async def clean():
    res = clean_db()
    if res:
        return {"result": "Database cleaned."}
    else:
        raise HTTPException(status_code=httpx.codes.INTERNAL_SERVER_ERROR, detail="Error cleaning database!")
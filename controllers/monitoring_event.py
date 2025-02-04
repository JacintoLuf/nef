import uuid
import httpx
from time import time
from fastapi import APIRouter, Request, Response, HTTPException, BackgroundTasks
from api.config import conf
from controllers.internal import send_notification
from models.created_ee_subscription import CreatedEeSubscription
from models.monitoring_event_subscription import MonitoringEventSubscription
from models.amf_created_event_subscription import AmfCreatedEventSubscription
import core.af_handler as af_handler
import core.amf_handler as amf_handler
import core.udm_handler as udm_handler
import crud.monitoringEventSubscription as monitoringEventSubscription


router = APIRouter()

@router.get("/3gpp-monitoring-event/v1/{scsAsId}/subscriptions/{subscriptionId}")
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

@router.get("/3gpp-monitoring-event/v1/{scsAsId}/subscriptions")
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

@router.post("/3gpp-monitoring-event/v1/{scsAsId}/subscriptions")
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
    if not mon_evt_sub.monitoring_type or mon_evt_sub.notification_destination:
        raise HTTPException(status_code=httpx.codes.BAD_REQUEST, detail='Message shall include SCS/AS Identifier, "Monitoring Type", "Notification Destination Address" and pne of External Identifier, MSISDN or External Group Identifier')
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
        return Response(status_code=res.status_code, headers=headers, content="Subscription creation failed!")
        


@router.put("/3gpp-monitoring-event/v1/{scsAsId}/subscriptions/{subscriptionId}")
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

@router.patch("/3gpp-monitoring-event/v1/{scsAsId}/subscriptions/{subscriptionId}")
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

@router.delete("/3gpp-monitoring-event/v1/{scsAsId}/subscriptions/{subscriptionId}")
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
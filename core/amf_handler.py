import json
import httpx
import uuid
from api.config import conf
from models.monitoring_event_subscription import MonitoringEventSubscription
from models.amf_create_event_subscription import AmfCreateEventSubscription
from models.amf_created_event_subscription import AmfCreatedEventSubscription
from models.amf_event_subscription import AmfEventSubscription
from models.amf_event import AmfEvent
from models.amf_event_mode import AmfEventMode
import crud.amfCreatedEventSubscription as amfCreatedEventSubscription

async def amf_event_exposure_subscribe():
    evt_list = [
        AmfEvent(
            type="REGISTRATION_STATE_REPORT",
            # immediate_flag=True,
            # max_reports=100,
            # report_ue_reachable=True
        ),
        AmfEvent(
            type="CONNECTIVITY_STATE_REPORT",
            immediate_flag=True,
            # max_reports=100,
            # report_ue_reachable=True
        ),
        # amf_evt3 = AmfEvent(
        #     type="LOSS_OF_CONNECTIVITY",
        #     # immediate_flag=True,
        #     # max_reports=100,
        #     report_ue_reachable=True
        # )
        AmfEvent(
            type="UES_IN_AREA_REPORT",
            # immediate_flag=True,
            # max_reports=100,
            report_ue_reachable=True
        )
    ]
    
    for evt in evt_list:
        amf_sub = AmfEventSubscription(
            event_list=[evt],
            event_notify_uri=f"http://{conf.HOSTS['NEF'][0]}/nnef-callback/amf-event-sub-callback",
            nf_id=conf.API_UUID,
            any_ue=True
        )
        amf_evt_sub = AmfCreateEventSubscription(subscription=amf_sub)
        async with httpx.AsyncClient(http1=True if conf.CORE=="free5gc" else False, http2=None if conf.CORE=="free5gc" else True) as client:
            response = await client.post(
                f"http://{conf.HOSTS['AMF'][0]}/namf-evts/v1/subscriptions",
                headers=conf.GLOBAL_HEADERS,
                data=json.dumps(amf_evt_sub.to_dict())
            )
            # conf.logger.info(f"AMF event subscribe headers: {response.headers}")
            conf.logger.info(f"AMF {evt.type} event subscribe resposne({response.status_code}): {response.text}")

    # if response.status_code==httpx.codes.CREATED:
    #     res_data = response.json()
    #     created_sub = AmfCreatedEventSubscription.from_dict(res_data)
    #     res = await amfCreatedEventSubscription.created_ee_subscriptionscription_insert(created_sub.subscription_id, created_sub)
    return response

async def amf_event_exposure_subscription_create(monEvtSub: MonitoringEventSubscription=None, afId: str=None, int_group_id: str = None):

    amf_events = [AmfEvent(
        type=monEvtSub.monitoring_type,
        max_reports=monEvtSub.maximum_number_of_reports,
        max_response_time=monEvtSub.maximum_response_time if monEvtSub.monitoring_type == "UE_REACHABILITY" else None,
        )]
    amf_event_mode = AmfEventMode(
        trigger="ONE_TIME" if monEvtSub.maximum_number_of_reports==1 else "PERIODIC" if monEvtSub.rep_period else "CONTINUOUS",
        max_reports=monEvtSub.maximum_number_of_reports,
        expiry=monEvtSub.monitor_expire_time,
        rep_period=monEvtSub.rep_period,
        # samp_ratio=monEvtSub.sampling_interval
    )

    amf_sub = AmfEventSubscription(
        event_list=amf_events,
        event_notify_uri=f"http://{conf.HOSTS['NEF'][0]}/nnef-callback/amf-event-sub-callback", #monEvtSub.notification_destination
        nf_id=conf.API_UUID,
        # any_ue=True,
        group_id=int_group_id,
        options=amf_event_mode,
        source_nf_type="AF"
    )
    # monitoring expiry time update in case recieved from amf or udm
    amf_evt_sub = AmfCreateEventSubscription(subscription=amf_sub)
    async with httpx.AsyncClient(http1=True if conf.CORE=="free5gc" else False, http2=None if conf.CORE=="free5gc" else True) as client:
        response = await client.post(
            f"http://{conf.HOSTS['AMF'][0]}/namf-evts/v1/subscriptions",
            headers=conf.GLOBAL_HEADERS,
            data=json.dumps(amf_evt_sub.to_dict())
        )
        conf.logger.info(f"Event sub response: {response.text}")
    return response

async def amf_event_exposure_subscription_update(app_session_id: str=None):
    if app_session_id:
        async with httpx.AsyncClient(http1=True if conf.CORE=="free5gc" else False, http2=None if conf.CORE=="free5gc" else True) as client:
            response = await client.post(
                f"http://{conf.HOSTS['AMF'][0]}/namf-evts/v1/subscriptions",
                headers=conf.GLOBAL_HEADERS
            )
            conf.logger.info(response.text)
        return response.json()
    return None

async def amf_event_exposure_subscription_delete(app_session_id: str=None):
    if app_session_id:
        async with httpx.AsyncClient(http1=True if conf.CORE=="free5gc" else False, http2=None if conf.CORE=="free5gc" else True) as client:
            response = await client.post(
                f"http://{conf.HOSTS['AMF'][0]}/namf-evts/v1/subscriptions",
                headers=conf.GLOBAL_HEADERS
            )
            conf.logger.info(response.text)
        return response.json()
    return None
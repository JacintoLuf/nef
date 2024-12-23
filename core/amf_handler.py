import json
import httpx
import uuid
from api.config import conf
from models.monitoring_event_subscription import MonitoringEventSubscription
from models.amf_create_event_subscription import AmfCreateEventSubscription
from models.amf_event_subscription import AmfEventSubscription
from models.amf_event import AmfEvent
from models.amf_event_mode import AmfEventMode

async def amf_event_exposure_subscribe():
    amf_evt = AmfEvent(
        type="REGISTRATION_STATE_REPORT",
        immediate_flag=True
    )
    amf_evt2 = AmfEvent(
        type="CONNECTIVITY_STATE_REPORT",
        immediate_flag=True
    )
    amf_evt3 = AmfEvent(
        type="LOSS_OF_CONNECTIVITY",
        immediate_flag=True
    )
    amf_evt4 = AmfEvent(
        type="UES_IN_AREA_REPORT",
        immediate_flag=True
    )
    amf_sub = AmfEventSubscription(
        event_list=[amf_evt, amf_evt2, amf_evt3, amf_evt4],
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
        conf.logger.info(f"AMF UE event status code: {response.status_code}")
        conf.logger.info(f"AMF UE event resposne: {response.text}")

async def amf_event_exposure_subscription_create(monEvtSub: MonitoringEventSubscription=None, afId: str=None, int_group_id: str = None):

    amf_events = [AmfEvent(
        type=monEvtSub.monitoring_type,
        max_reports=monEvtSub.maximum_number_of_reports,
        max_response_time=monEvtSub.maximum_response_time if monEvtSub.monitoring_typ == "UE_REACHABILITY" else None,
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
        event_notify_uri=f"http://{conf.HOSTS['NEF'][0]}/nnef-callback/amf-event-sub-callback",
        nf_id=conf.API_UUID,
        # any_ue=True,
        group_id=int_group_id,
        options=amf_event_mode,
        source_nf_type="AF"
    )
    # monitoring expiry time update in case recieved from amf or udm
    return

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
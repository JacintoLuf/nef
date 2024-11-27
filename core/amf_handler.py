import json
import httpx
from api.config import conf
from models.amf_create_event_subscription import AmfCreateEventSubscription
from models.amf_event_subscription import AmfEventSubscription
from models.amf_event import AmfEvent

async def amf_event_exposure_subscribe():
    amf_evt = AmfEvent(
        type="REGISTRATION_STATE_REPORT",
        immediate_flag=True
    )
    amf_evt2 = AmfEvent(
        type="CONNECTIVITY_STATE_REPORT",
        immediate_flag=True
    )
    amf_sub = AmfEventSubscription(
        event_list=[amf_evt, amf_evt2],
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
        conf.logger.info(response.text)

async def amf_event_exposure_subscription_create(app_session_id: str=None):

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
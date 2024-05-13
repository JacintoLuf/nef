import httpx
import json
from api.config import conf
from models.monitoring_event_subscription import MonitoringEventSubscription
from models.ee_subscription import EeSubscription
from models.created_ee_subscription import CreatedEeSubscription
from models.monitoring_configuration import MonitoringConfiguration

async def udm_sdm_id_translation(ueId: str=None):
    print(f"id to translate {ueId}")
    try:
        async with httpx.AsyncClient(http1=True if conf.CORE=="free5gc" else False, http2=None if conf.CORE=="free5gc" else True) as client:
            response = await client.get(
                f"http://{conf.HOSTS['UDM'][0]}/nudm-sdm/v2/{ueId}/id-translation-result",
                headers=conf.GLOBAL_HEADERS
            )
            print(response.text)
    except Exception as e:
        print(e.__str__)
    return response

async def udm_sdm_group_identifiers_translation(ext_group_id: str=None):
    params = {'ext_group_id': ext_group_id}

    async with httpx.AsyncClient(http1=False, http2=True) as client:
        response = await client.get(
            f"http://{conf.HOSTS['UDM'][0]}/nudm-sdm/v2/group-data/group-identifiers",
            headers=conf.GLOBAL_HEADERS,
            params=params
        )
        print(response.text)

    return response

async def udm_ee_subscription_create(monEvtSub: MonitoringEventSubscription=None, afId: str=None):
    ueIdentity = "^anyUE$"

    mon_conf = {
        '1': MonitoringConfiguration(event_type="LOSS_OF_CONNECTIVITY", immediate_flag=True),
        '2': MonitoringConfiguration(event_type="ACCESS_TYPE_REPORT", immediate_flag=True),
        '3': MonitoringConfiguration(event_type="PDN_CONNECTIVITY_STATUS", immediate_flag=True),
        '4': MonitoringConfiguration(event_type="UE_CONNECTION_MANAGEMENT_STATE", immediate_flag=True),
        '5': MonitoringConfiguration(event_type="ACCESS_TYPE_REPORT", immediate_flag=True),
        '6': MonitoringConfiguration(event_type="REGISTRATION_STATE_REPORT", immediate_flag=True),
        '7': MonitoringConfiguration(event_type="CONNECTIVITY_STATE_REPORT", immediate_flag=True),
        '8': MonitoringConfiguration(event_type="PDU_SES_REL", immediate_flag=True),
        '9': MonitoringConfiguration(event_type="PDU_SES_EST", immediate_flag=True)
        }

    ee_sub = EeSubscription(
        callback_reference=f"http://{conf.HOSTS['NEF'][0]}/nnef-callback/udm-event-sub-callback",
        monitoring_configurations=mon_conf,
        # reporting_options="",
        # supported_features="",
    )
    async with httpx.AsyncClient(http1=True if conf.CORE=="free5gc" else False, http2=None if conf.CORE=="free5gc" else True) as client:
        response = await client.post(
            f"http://{conf.HOSTS['UDM'][0]}/nudm-ee/v1/{ueIdentity}/ee-subscriptions",
            headers=conf.GLOBAL_HEADERS,
            data=json.dumps(ee_sub.to_dict())
        )
        print(response.text)

    if response.status_code==httpx.codes.CREATED:
        res_data = await response.json()
        created_sub = CreatedEeSubscription.from_dict(res_data)

    return response
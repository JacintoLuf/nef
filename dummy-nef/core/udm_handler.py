import httpx
import json
import datetime
from datetime import datetime, timezone, timedelta
from api.config import conf
from models.monitoring_event_subscription import MonitoringEventSubscription
from models.ee_subscription import EeSubscription
from models.created_ee_subscription import CreatedEeSubscription
from models.monitoring_configuration import MonitoringConfiguration
from models.reporting_options import ReportingOptions
import crud.createdEeSubscription as createdEeSubscription

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
    ueIdentity = "anyUE"

    if monEvtSub:
        mon_conf = {'1': MonitoringConfiguration(event_type=monEvtSub.monitoring_type, immediate_flag=True if monEvtSub.maximum_number_of_reports==1 else False, af_id=afId)}
        repo_opt = ReportingOptions(
            report_mode=None,
            max_num_of_reports=monEvtSub.maximum_number_of_reports,
            expiry=monEvtSub.monitor_expire_time,
            sampling_ratio=monEvtSub.sampling_interval,
            guard_time=monEvtSub.group_report_guard_time,
            report_period=monEvtSub.rep_period,
            notif_flag=None
        )
    else:
        mon_conf = {
            '1': MonitoringConfiguration(event_type="LOSS_OF_CONNECTIVITY"),
            '2': MonitoringConfiguration(event_type="ACCESS_TYPE_REPORT"),
            '3': MonitoringConfiguration(event_type="PDN_CONNECTIVITY_STATUS"),
            '4': MonitoringConfiguration(event_type="UE_CONNECTION_MANAGEMENT_STATE"),
            '5': MonitoringConfiguration(event_type="ACCESS_TYPE_REPORT"),
            '6': MonitoringConfiguration(event_type="REGISTRATION_STATE_REPORT"),
            '7': MonitoringConfiguration(event_type="CONNECTIVITY_STATE_REPORT"),
            '8': MonitoringConfiguration(event_type="PDU_SES_REL"),
            '9': MonitoringConfiguration(event_type="PDU_SES_EST")
        }
        current_time = datetime.now(timezone.utc)
        validity_time = current_time + timedelta(days=1)
        formatted_time = validity_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        repo_opt = ReportingOptions(
            report_mode="ON_EVENT_DETECTION",
            max_num_of_reports=1000,
            expiry=formatted_time
        )

    ee_sub = EeSubscription(
        callback_reference=f"http://{conf.HOSTS['NEF'][0]}/nnef-callback/udm-event-sub-callback",
        monitoring_configurations=mon_conf,
        reporting_options=repo_opt,
        # supported_features="",
        epc_applied_ind=False,
        notify_correlation_id=1,
        second_callback_ref=f"http://{conf.HOSTS['NEF'][0]}/nnef-callback/udm-event-sub-callback"
    )
    print(ee_sub.to_dict())
    async with httpx.AsyncClient(http1=True if conf.CORE=="free5gc" else False, http2=None if conf.CORE=="free5gc" else True) as client:
        response = await client.post(
            f"http://{conf.HOSTS['UDM'][0]}/nudm-ee/v1/{ueIdentity}/ee-subscriptions",
            headers=conf.GLOBAL_HEADERS,
            data=json.dumps(ee_sub.to_dict())
        )
        print(response.headers)
        print(response.text)

    if response.status_code==httpx.codes.CREATED:
        res_data = response.json()
        print(f"udm response data: {res_data}")
        created_sub = CreatedEeSubscription.from_dict(res_data)
        if response.headers['location']:
            res = createdEeSubscription.created_ee_subscriptionscription_insert(created_sub)

async def udm_ee_subscription_udoate(monEvtSub: MonitoringEventSubscription=None, afId: str=None):

    return

async def udm_ee_subscription_delete(monEvtSub: MonitoringEventSubscription=None, afId: str=None):
    
    return
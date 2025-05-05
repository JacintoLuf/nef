import httpx
import json
import uuid
from api.config import conf
from models.ue_id_req import UeIdReq
from models.monitoring_event_subscription import MonitoringEventSubscription
from models.ee_subscription import EeSubscription
from models.created_ee_subscription import CreatedEeSubscription
from models.monitoring_configuration import MonitoringConfiguration
from models.reporting_options import ReportingOptions
from models.location_reporting_configuration import LocationReportingConfiguration
from models.pdu_session_status_cfg import PduSessionStatusCfg

async def udm_sdm_id_translation(ueId: str=None, ue_req: UeIdReq=None):
    conf.logger.info(f"id to translate {ueId}")
    params = {}
    if ue_req:
        if ue_req.app_port_id:
            params['app-port-id'] = ue_req.app_port_id
        if ue_req.mtc_provider_id:
            params['mtc-provider-info'] = ue_req.mtc_provider_id
        if ue_req.af_id:
            params['af-id'] = ue_req.af_id

    try:
        version = "v1" if conf.CORE=="free5gc" else "v2"
        async with httpx.AsyncClient(http1=True if conf.CORE=="free5gc" else False, http2=None if conf.CORE=="free5gc" else True) as client:
            response = await client.get(
                f"http://{conf.HOSTS['UDM'][0]}/nudm-sdm/{version}/{ueId}/id-translation-result",
                headers=conf.GLOBAL_HEADERS,
                params=params
            )
            conf.logger.info(f"UDM status code: {response.status_code}")
            conf.logger.info(f"UDM resposne: {response.text}")
    except Exception as e:
        conf.logger.info(e.__str__)
    return response

async def udm_sdm_group_identifiers_translation(ext_group_id: str=None):
    params = {'ext_group_id': ext_group_id}
    
    version = "v1" if conf.CORE=="free5gc" else "v2"
    async with httpx.AsyncClient(http1=True if conf.CORE=="free5gc" else False, http2=None if conf.CORE=="free5gc" else True) as client:
        response = await client.get(
            f"http://{conf.HOSTS['UDM'][0]}/nudm-sdm/{version}/group-data/group-identifiers",
            headers=conf.GLOBAL_HEADERS,
            params=params
        )
        conf.logger.info(response.text)
    return response

async def udm_event_exposure_subscribe(monEvtSub: MonitoringEventSubscription=None, afId: str=None):
    ueIdentity = "anyUE"
    loc_conf = LocationReportingConfiguration(current_location=True)
    pdu_conf = PduSessionStatusCfg("internet")
    mon_conf = {
        # '1': MonitoringConfiguration(event_type="LOSS_OF_CONNECTIVITY"),
        '2': MonitoringConfiguration(event_type="LOCATION_REPORTING", location_reporting_configuration=loc_conf),
        '3': MonitoringConfiguration(event_type="PDN_CONNECTIVITY_STATUS", immediate_flag=True, pdu_session_status_cfg=pdu_conf),
    }
    # repo_opt = ReportingOptions(
    #     report_mode="ON_EVENT_DETECTION",
    #     max_num_of_reports=1000,
    # )

    ee_sub = EeSubscription(
        callback_reference=f"http://{conf.HOSTS['NEF'][0]}/nnef-callback/udm-event-sub-callback",
        monitoring_configurations=mon_conf,
        # reporting_options=repo_opt,
        # supported_features="1",
        notify_correlation_id=str(uuid.uuid4().hex),
        second_callback_ref=f"http://{conf.HOSTS['NEF'][0]}/nnef-callback/udm-event-sub-callback"
    )
    # conf.logger.info(ee_sub.to_dict())
    async with httpx.AsyncClient(http1=True if conf.CORE=="free5gc" else False, http2=None if conf.CORE=="free5gc" else True) as client:
        response = await client.post(
            f"http://{conf.HOSTS['UDM'][0]}/nudm-ee/v1/{ueIdentity}/ee-subscriptions",
            headers=conf.GLOBAL_HEADERS,
            data=json.dumps(ee_sub.to_dict())
        )
        try:
            data_dict = response.json()
            created_evt = CreatedEeSubscription.from_dict(data_dict)
            if not created_evt.event_reports:
                conf.logger.info(f"UDM event subscribe resposne({response.status_code}): No reports")
            else:
                for report in created_evt.event_reports:
                    conf.logger.info(f"{report.event_type}: {report}")
        except Exception as e:
            conf.logger.info(e)
    # if response.status_code==httpx.codes.CREATED:
    #     res_data = response.json()
    #     created_sub = CreatedEeSubscription.from_dict(res_data)
    #     res = await createdEeSubscription.created_ee_subscriptionscription_insert(ee_sub.notify_correlation_id, created_sub)
    return response

async def udm_event_exposure_subscription_create(monEvtSub: MonitoringEventSubscription=None, ueIdentity: str=None, afId: str=None, _id: str=None):
    mon_configs = {'1': MonitoringConfiguration(
        event_type=monEvtSub.monitoring_type,
        # location_reporting_configuration= monEvtSub.location_area if monEvtSub.monitoring_type == "LOCATION_REPORTING" else None,
        # association_type=,
        # datalink_report_cfg=,
        # loss_connectivity_cfg=,
        maximum_latency=monEvtSub.maximum_latency if monEvtSub.monitoring_type == "UE_REACHABILITY_FOR_DATA" else None,
        maximum_response_time=monEvtSub.maximum_response_time if monEvtSub.monitoring_type == "UE_REACHABILITY_FOR_DATA" else None,
        suggested_packet_num_dl=monEvtSub.suggested_number_of_dl_packets if monEvtSub.monitoring_type == "UE_REACHABILITY_FOR_DATA" else None,
        # reachability_for_data_cfg=monEvtSub if monEvtSub.monitoring_type == "UE_REACHABILITY_FOR_DATA" else None,
        pdu_session_status_cfg=monEvtSub if monEvtSub.monitoring_type == "PDN_CONNECTIVITY_STATUS" else None,
        af_id=afId,
        idle_status_ind=monEvtSub.idle_status_indication if monEvtSub.monitoring_type == "UE_REACHABILITY_FOR_DATA" or monEvtSub.monitoring_type == "AVAILABILITY_AFTER_DDN_FAILURE" else None
    )}
    
    rep_opts = ReportingOptions(
        report_mode="PERIODIC" if monEvtSub.maximum_number_of_reports > 1 or monEvtSub.monitor_expire_time else "ON_EVENT_DETECTION",
        max_num_of_reports=monEvtSub.maximum_number_of_reports,
        expiry=monEvtSub.monitor_expire_time,
        # sampling_ratio=monEvtSub,
        report_period=monEvtSub.rep_period,
    )

    ee_sub = EeSubscription(
        callback_reference=f"http://{conf.HOSTS['NEF'][0]}/nnef-callback/udm-event-sub-callback/{_id}",
        monitoring_configurations=mon_configs,
        reporting_options=rep_opts,
        # supported_features="fffff",
        notify_correlation_id=str(uuid.uuid4()),
        second_callback_ref=f"http://{conf.HOSTS['NEF'][0]}/nnef-callback/udm-event-sub-callback/{_id}"
    )

    async with httpx.AsyncClient(http1=True if conf.CORE=="free5gc" else False, http2=None if conf.CORE=="free5gc" else True) as client:
        response = await client.post(
            f"http://{conf.HOSTS['UDM'][0]}/nudm-ee/v1/{ueIdentity}/ee-subscriptions",
            headers=conf.GLOBAL_HEADERS,
            data=json.dumps(ee_sub.to_dict())
        )
        conf.logger.info(response.text)
    return response

async def udm_event_exposure_subscription_update(monEvtSub: MonitoringEventSubscription=None, afId: str=None):

    return

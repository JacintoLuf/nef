import httpx
import json
from api.config import conf
from models.monitoring_report import MonitoringReport
from models.amf_event_report import AmfEventReport
from models.monitoring_notification import MonitoringNotification
from models.monitoring_event_report import MonitoringEventReport
from models.pdn_connection_information import PdnConnectionInformation
from models.event_notification import EventNotification
import crud.trafficInfluSub as trafficInfluSub
from models.traffic_influ_sub import TrafficInfluSub

async def af_monitoring_notification_post(mon_rep: MonitoringReport=None, amf_evt_rep: AmfEventReport=None):
    mon_notif = MonitoringNotification()
    mon_evt_rep = MonitoringEventReport()

    if mon_rep:
        conn_info = PdnConnectionInformation(status=mon_rep.report.pdn_conn_stat,
                                             pdn_type=mon_rep.report.pdu_sess_type,
                                             ipv4_addr=mon_rep.report.ipv4_addr,
                                             ipv6_p=mon_rep.report.ipv6_addrs,
                                             ) if mon_rep.report else None
        mon_evt_rep.monitoring_type = mon_rep.event_type
        mon_evt_rep.event_time = mon_rep.time_stamp
        mon_evt_rep.roaming_status = mon_rep.report.roaming
        mon_evt_rep.loss_of_connect_reason = mon_rep.report.loss_of_connect_reason
        mon_evt_rep.pdn_conn_info_list = [conn_info]
    elif amf_evt_rep:
        mon_evt_rep.monitoring_type = amf_evt_rep.type
        mon_evt_rep.idle_status_info = amf_evt_rep.idle_status_indication
        mon_evt_rep.location_info = amf_evt_rep.location
        mon_evt_rep.loss_of_connect_reason = amf_evt_rep.loss_of_connect_reason
        mon_evt_rep.max_ue_availability_time = amf_evt_rep.max_availability_time

    mon_notif.monitoring_event_reports = [mon_evt_rep]

    try:
        async with httpx.AsyncClient(http1=False, http2=True) as client:
            response = await client.post(
                "",
                headers=conf.GLOBAL_HEADERS,
                data=json.dumps(mon_notif.to_dict())
            )
            conf.logger.info(response.text)
    except Exception as e:
        conf.logger.info(e.__str__)
    return response

async def af_imidiate_report(mon_rep: MonitoringReport=None, amf_evt_rep: AmfEventReport=None):
    mon_notif = MonitoringEventReport()

    if mon_rep:
        conn_info = PdnConnectionInformation(status=mon_rep.report.pdn_conn_stat,
                                             pdn_type=mon_rep.report.pdu_sess_type,
                                             ipv4_addr=mon_rep.report.ipv4_addr,
                                             ipv6_p=mon_rep.report.ipv6_addrs,
                                             ) if mon_rep.report else None
        mon_notif.monitoring_type = mon_rep.event_type
        mon_notif.event_time = mon_rep.time_stamp
        mon_notif.roaming_status = mon_rep.report.roaming
        mon_notif.loss_of_connect_reason = mon_rep.report.loss_of_connect_reason
        mon_notif.pdn_conn_info_list = [conn_info]
    elif amf_evt_rep:
        mon_notif.monitoring_type = amf_evt_rep.type
        mon_notif.idle_status_info = amf_evt_rep.idle_status_indication
        mon_notif.location_info = amf_evt_rep.location
        mon_notif.loss_of_connect_reason = amf_evt_rep.loss_of_connect_reason
        mon_notif.max_ue_availability_time = amf_evt_rep.max_availability_time

    return mon_notif

async def af_up_path_chg_notif(subId: str, evt_notif: EventNotification):
    sub_dict = trafficInfluSub.traffic_influence_subscription_get(subId=subId)
    sub = TrafficInfluSub.from_dict(sub_dict['sub'])
    try:
        async with httpx.AsyncClient(http1=False, http2=True) as client:
            response = await client.post(
                sub.notification_destination,
                headers=conf.GLOBAL_HEADERS,
                data=json.dumps(evt_notif.to_dict())
            )
            conf.logger.info(response.text)
    except Exception as e:
        conf.logger.info(e.__str__)
    return response
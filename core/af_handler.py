import httpx
import json
import uuid
import datetime
from datetime import datetime, timezone, timedelta
from api.config import conf
from models.monitoring_report import MonitoringReport
from models.amf_event_report import AmfEventReport
from models.monitoring_notification import MonitoringNotification
from models.config_result import ConfigResult
from models.monitoring_event_report import MonitoringEventReport

async def af_monitoring_notification_post(mon_rep: MonitoringReport=None, amf_evt_rep: AmfEventReport=None):
    mon_notif = MonitoringNotification()

    if mon_rep:
        mon_notif
    elif amf_evt_rep:
        mon_notif

    try:
        async with httpx.AsyncClient(http1=True if conf.CORE=="free5gc" else False, http2=None if conf.CORE=="free5gc" else True) as client:
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
    af_mon_rep = MonitoringEventReport()

    if mon_rep:
        af_mon_rep
    elif amf_evt_rep:
        af_mon_rep

    return 
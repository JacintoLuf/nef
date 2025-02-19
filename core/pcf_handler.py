import json
import httpx
from api.config import conf
from models.events_subsc_req_data import EventsSubscReqData
from models.pcf_binding import PcfBinding
from models.traffic_influ_sub import TrafficInfluSub
from models.as_session_with_qo_s_subscription import AsSessionWithQoSSubscription
from models.app_session_context import AppSessionContext
from models.app_session_context_req_data import AppSessionContextReqData
from models.af_routing_requirement import AfRoutingRequirement
from models.af_event_subscription import AfEventSubscription
from models.media_component import MediaComponent
from models.media_sub_component import MediaSubComponent
from models.tsn_qos_container import TsnQosContainer

async def pcf_policy_authorization_get(app_session_id: str=None):
    if app_session_id:
        async with httpx.AsyncClient(http1=True if conf.CORE=="free5gc" else False, http2=None if conf.CORE=="free5gc" else True) as client:
            response = await client.get(
                f"http://{conf.HOSTS['PCF'][0]}/npcf-policyauthorization/v1/app-sessions/{app_session_id}",
                headers={'Accept': 'application/json,application/problem+json'}
            )
            conf.logger.info(response.text)
            res = await response.json()
            if res:
                return res
    return None

async def pcf_policy_authorization_create_ti(binding: PcfBinding=None, traffic_influ_sub: TrafficInfluSub=None, _id: str=None):
    host_addr = f"{binding.pcf_ip_end_points[0].ipv4_address}:7777" if binding is not None else conf.HOSTS['PCF'][0]

    req_data = AppSessionContextReqData()
    for attr_name in traffic_influ_sub.attribute_map.keys():
        attr_val = getattr(traffic_influ_sub, attr_name)
        if attr_name == 'ipv4_addr':
            setattr(req_data, 'ue_ipv4', attr_val)
        elif attr_name == 'ipv6_addr':
            setattr(req_data, 'ue_ipv6', attr_val)
        elif attr_name == 'mac_addr':
            setattr(req_data, 'ue_mac', attr_val)
        elif attr_name == 'snssai':
            setattr(req_data, 'slice_info', attr_val)
        # elif attr_name == 'notification_destination':
        #     setattr(req_data, 'notif_uri', attr_val)
        elif hasattr(req_data, attr_name) and attr_val:
            setattr(req_data, attr_name, attr_val)

    req_data.notif_uri = f"http://{conf.HOSTS['NEF'][0]}/nnef-callback/nsmf_up_path_change/{_id}"
    req_data.supp_feat = conf.SERVICE_NAMES['3gpp-traffic-influence']
    rout_req = AfRoutingRequirement(
            app_reloc=not traffic_influ_sub.app_relo_ind if traffic_influ_sub.app_relo_ind else None,
            route_to_locs=traffic_influ_sub.traffic_routes,
            sp_val=traffic_influ_sub.valid_geo_zone_ids,
            temp_vals=traffic_influ_sub.temp_validities,
            addr_preser_ind=traffic_influ_sub.addr_preser_ind,
        )
    
    if not traffic_influ_sub.af_app_id:
        med_sub_cmp = {}
        for idx, f in enumerate(traffic_influ_sub.traffic_filters):
            med_sub_cmp[f.flow_id] = MediaSubComponent(f_num=f.flow_id, f_descs=f.flow_descriptions)
        med_comps = MediaComponent(af_app_id=traffic_influ_sub.af_app_id,
                                    af_rout_req=rout_req,
                                    med_comp_n=1,
                                    f_status="ENABLED", #DISABLED
                                    med_type="AUDIO",
                                    med_sub_comps=med_sub_cmp)
        req_data.med_components = {f'{med_comps.med_comp_n}': med_comps}
    req_data.af_rout_req = rout_req
    app_session_context = AppSessionContext(asc_req_data=req_data)

    conf.logger.info("Creating app session for traffic influence at PCF")
    async with httpx.AsyncClient(http1=True if conf.CORE=="free5gc" else False, http2=None if conf.CORE=="free5gc" else True) as client:
        response = await client.post(
            f"http://{host_addr}/npcf-policyauthorization/v1/app-sessions",
            headers={'Accept': 'application/json,application/problem+json', 'content-type': 'application/json'},
            data=json.dumps(app_session_context.to_dict())
        )
        conf.logger.info(f"Response {response.status_code} for creating app session. Content: {response.text}")
    return response

async def pcf_policy_authorization_create_qos(binding: PcfBinding=None, as_session_qos_sub: AsSessionWithQoSSubscription=None, _id: str=None):
    host_addr = f"{binding.pcf_ip_end_points[0].ipv4_address}:7777" if binding is not None else conf.HOSTS['PCF'][0]

    req_data = AppSessionContextReqData()
    for attr_name in as_session_qos_sub.attribute_map.keys():
        attr_val = getattr(as_session_qos_sub, attr_name)
        if attr_name == 'ue_ipv4_addr':
            setattr(req_data, 'ue_ipv4', attr_val)
        elif attr_name == 'ue_ipv6_addr':
            setattr(req_data, 'ue_ipv6', attr_val)
        elif attr_name == 'mac_addr':
            setattr(req_data, 'ue_mac', attr_val)
        elif attr_name == 'snssai':
            setattr(req_data, 'slice_info', attr_val)
        # elif attr_name == 'notification_destination':
        #     setattr(req_data, 'notif_uri', attr_val)
        elif hasattr(req_data, attr_name) and attr_val:
            setattr(req_data, attr_name, attr_val)

    req_data.notif_uri = f"http://{conf.HOSTS['NEF'][0]}/nnef-callback/pcf_qos_notif/{_id}"
    req_data.supp_feat = 'ffffff' # conf.SERVICE_NAMES['3gpp-as-session-with-qos']
    tsn_qos_c = None
    if as_session_qos_sub.tsc_qos_req:
        tsn_qos_c = TsnQosContainer(
            max_tsc_burst_size=as_session_qos_sub.tsc_qos_req.max_tsc_burst_size,
            tsc_pack_delay=as_session_qos_sub.tsc_qos_req.req5_gsdelay,
            tsc_prio_level=as_session_qos_sub.tsc_qos_req.priority,
        )

    med_sub_cmp = {}
    for idx, f in enumerate(as_session_qos_sub.flow_info):
        med_sub_cmp[f.flow_id] = MediaSubComponent(f_num=f.flow_id, f_descs=f.flow_descriptions)
    med_comps = MediaComponent(qos_reference=as_session_qos_sub.qos_reference,
                               alt_ser_reqs=as_session_qos_sub.alt_qo_s_references,
                               alt_ser_reqs_data=as_session_qos_sub.alt_qos_reqs,
                               med_comp_n=0,
                               f_status="ENABLED",
                               med_type=conf.QCI_MAP[as_session_qos_sub.qos_reference], #"AUDIO",
                               med_sub_comps=med_sub_cmp,
                            #    res_prio="PRIO_1", ???????????????????
                               tsn_qos=tsn_qos_c)
    req_data.med_components = {f'{med_comps.med_comp_n}': med_comps}
    conf.logger.info(f"--------------------------------med comps------------------------------\n\
                     {med_comps.to_str()}\n---------------------------------------------------------------------")
    app_session_context = AppSessionContext(asc_req_data=req_data)

    if as_session_qos_sub.events:
        af_evt_subs = []
        for evt in as_session_qos_sub.events:
            af_evt_sub = AfEventSubscription(event=evt)
            if as_session_qos_sub.qos_mon_info:
                # af_evt_sub.notif_method = as_session_qos_sub.qos_mon_info.notif_method
                af_evt_sub.rep_period = as_session_qos_sub.qos_mon_info.rep_period
                af_evt_sub.wait_time = as_session_qos_sub.qos_mon_info.wait_time
            af_evt_subs.append(af_evt_sub)
        evt_sub_req_data = EventsSubscReqData()
        evt_sub_req_data.events = af_evt_subs
        evt_sub_req_data.notif_uri = f"http://{conf.HOSTS['NEF'][0]}/nnef-callback/pcf_qos_notif/{_id}"
        evt_sub_req_data.usg_thres = as_session_qos_sub.usage_threshold
        evt_sub_req_data.notif_corre_id = _id
        if as_session_qos_sub.qos_mon_info:
            evt_sub_req_data.req_qos_mon_params = as_session_qos_sub.qos_mon_info.req_qos_mon_params
            evt_sub_req_data.qos_mon.rep_thresh_dl = as_session_qos_sub.qos_mon.rep_thresh_dl
            evt_sub_req_data.qos_mon.rep_thresh_ul = as_session_qos_sub.qos_mon.rep_thresh_ul
            evt_sub_req_data.qos_mon.rep_thresh_rp = as_session_qos_sub.qos_mon.rep_thresh_rp
        req_data.ev_subsc = evt_sub_req_data

    conf.logger.info(f"-------------------------app session context---------------------------\n\
                    {app_session_context.to_str()}\n------------------------------------------------------------------------")
    conf.logger.info("Creating app session for as session with qos at PCF")
    async with httpx.AsyncClient(http1=True if conf.CORE=="free5gc" else False, http2=None if conf.CORE=="free5gc" else True) as client:
        response = await client.post(
            f"http://{host_addr}/npcf-policyauthorization/v1/app-sessions",
            headers={'Accept': 'application/json,application/problem+json', 'content-type': 'application/json'},
            data=json.dumps(app_session_context.to_dict())
        )
        conf.logger.info(f"Response {response.status_code} for creating app session. Content: {response.text}")
    return response

async def pcf_policy_authorization_delete(subId: str=None):
    conf.logger.info(f"Deleting app session {subId} at PCF")
    async with httpx.AsyncClient(http1=True if conf.CORE=="free5gc" else False, http2=None if conf.CORE=="free5gc" else True) as client:
        response = await client.post(
            f"http://{conf.HOSTS['PCF'][0]}/npcf-policyauthorization/v1/app-sessions/{subId}/delete",
            headers={'Accept': 'application/json,application/problem+json'},
        )
        conf.logger.info(f"Response {response.status_code} for deleting app session. Content: {response.text}")
    return response
import json
import httpx
from typing import List
from api.config import conf
from models.app_session_context import AppSessionContext
from models.app_session_context_req_data import AppSessionContextReqData
from models.af_routing_requirement import AfRoutingRequirement
from models.traffic_influ_sub import TrafficInfluSub
from models.pcf_binding import PcfBinding
from models.media_component import MediaComponent

async def pcf_policy_authorization_get(app_session_id: str=None):
    if app_session_id:
        async with httpx.AsyncClient(http1=False, http2=True) as client:
            response = await client.get(
                f"http://{conf.HOSTS['PCF'][0]}:7777/npcf-policyauthorization/v1/app-sessions/{conf.NEF_PROFILE.nf_instance_id}",
                headers={'Accept': 'application/json,application/problem+json'}
            )
            print(response.text)
            #app_session_context = AppSessionContext.from_dict(response.json())
        return response.json()

async def pcf_policy_authorization_create(binding: PcfBinding=None, traffic_influ_sub: TrafficInfluSub=None):
    host_addr = binding.pcf_ip_end_points.ipv4_address or conf.HOSTS['PCF'][0]

    req_data = AppSessionContextReqData(slice_info=traffic_influ_sub.snssai)
    for attr_name in traffic_influ_sub.attribute_map.keys():
        attr_val = getattr(traffic_influ_sub, attr_name)
        if attr_name == 'ipv4_addr':
            setattr(req_data, 'ue_ipv4', attr_val)
        elif attr_name == 'ipv6_addr':
            setattr(req_data, 'ue_ipv6', attr_val)
        elif attr_name == 'mac_addr':
            setattr(req_data, 'ue_mac', attr_val)
        elif hasattr(req_data, attr_name) and attr_val:
            setattr(req_data, attr_name, attr_val)
    
    for attr_name in binding.attribute_map.keys():
        if hasattr(req_data, attr_name) and attr_val:
            setattr(req_data, attr_name, attr_val)

    req_data.notif_uri = f"http://{conf.HOSTS['NEF'][0]}:80/pcf-policy-authorization-callback"                
    if traffic_influ_sub.af_app_id != None:
        print(f"app id: {traffic_influ_sub.af_app_id}")
        rout_req = AfRoutingRequirement(
            app_reloc=traffic_influ_sub.app_relo_ind,
            route_to_locs=traffic_influ_sub.traffic_routes,
            temp_vals=traffic_influ_sub.temp_validities,
            addr_preser_ind=traffic_influ_sub.addr_preser_ind,
        )
        req_data.af_rout_req = rout_req
    else:
        req_data.med_components = MediaComponent(af_rout_req=rout_req)
        req_data.af_rout_req = rout_req
    app_session_context = AppSessionContext(asc_req_data=req_data)

    print("pcf app session context request")
    print(app_session_context)
    async with httpx.AsyncClient(http1=False, http2=True) as client:
            response = await client.post(
                f"http://{host_addr}:7777/npcf-policyauthorization/v1/app-sessions",
                headers={'Accept': 'application/json,application/problem+json', 'content-type': 'application/json'},
                data=json.dumps(app_session_context.to_dict())
            )
            print("pcf app session context response")
            print(response.text)

    return response

async def pcf_policy_authorization_delete(subId: str=None):

    async with httpx.AsyncClient(http1=False, http2=True) as client:
            response = await client.post(
                f"http://{conf.HOSTS['PCF'][0]}:7777/npcf-policyauthorization/v1/app-sessions/{subId}/delete",
                headers={'Accept': 'application/json,application/problem+json'},
            )
            print(response.text)

    return response
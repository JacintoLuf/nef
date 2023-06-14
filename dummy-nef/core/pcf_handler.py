from typing import List
import httpx
from api.config import conf
from models.app_session_context import AppSessionContext
from models.app_session_context_req_data import AppSessionContextReqData
from models.traffic_influ_sub import TrafficInfluSub

async def pcf_policy_authorization_get(app_session_id: str=None):
    if app_session_id:
        async with httpx.AsyncClient(http1=False, http2=True) as client:
            response = await client.get(
                f"http://{conf.HOSTS['PCF'][0]}:7777/npcf-policyauthorization/v1/app-sessions/{app_session_id}",
                headers={'Accept': 'application/json,application/problem+json'}
            )
            print(response.text)
            #app_session_context = AppSessionContext.from_dict(response.json())
        return None #app_session_context

async def pcf_policy_authorization_create(pcf_addr: List[str]=None, traffic_influ_sub: TrafficInfluSub=None) -> int:
    print(pcf_addr)
    if not pcf_addr or not traffic_influ_sub:
        return None
    
    traffic_influ_sub_attr = vars(traffic_influ_sub)
    req_data = AppSessionContextReqData()
    for attr_name, attr_val in traffic_influ_sub_attr.items():
        if hasattr(req_data, attr_name) and attr_name != 'swagger_types':
            print(f"name: {attr_name}, type: {type(attr_val)}")
            setattr(req_data, attr_name, attr_val)
    
    app_session_context = AppSessionContext(asc_req_data=req_data)

    async with httpx.AsyncClient(http1=False, http2=True) as client:
            response = await client.post(
                f"http://{pcf_addr or conf.HOSTS['PCF'][0]}:7777/npcf-policyauthorization/v1/app-sessions",
                headers={'Accept': 'application/json,application/problem+json'},
                data=app_session_context
            )
            print(response.text)
    # if response.status_code == httpx.codes.SEE_OTHER:
    #     print(response.text)

    return response.status_code

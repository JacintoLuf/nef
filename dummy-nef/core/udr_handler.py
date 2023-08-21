import httpx
import json
from typing import List
from api.config import conf
from models.traffic_influ_sub import TrafficInfluSub
from models.traffic_influ_data import TrafficInfluData
from models.traffic_influ_sub_patch import TrafficInfluSubPatch
from models.traffic_influ_data_patch import TrafficInfluDataPatch

async def udr_app_data_retrieval(loc: str=None):
    uri = loc or f"http://{conf.HOSTS['UDR'][0]}:7777/nudr-dr/v1/application-data/influenceData"
    #params = {'dnn': "", 'snssai': '', 'internal-Group-Id': '', 'supi': ''}
    async with httpx.AsyncClient(http1=False, http2=True) as client:
            response = await client.get(
                uri,
                headers={'Accept': 'application/json,application/problem+json'},
                #params=params
            )
            print(response.text)

    return response.status_code

async def udr_app_data_insert(traffic_influ_sub: TrafficInfluSub, intGroupID=None, supi=None):
    traffic_influ_data = TrafficInfluData()
    
    for attr_name in traffic_influ_sub.attribute_map.keys():
        attr_val = getattr(traffic_influ_sub, attr_name)
        if attr_name == 'tfcCorrInd':
            setattr(traffic_influ_data, 'traff_corre_ind', attr_val)
        elif attr_name == 'notificationDestination':
            setattr(traffic_influ_data, 'up_path_chg_notif_uri', attr_val)
        elif attr_name == 'tempValidities' and attr_val and len(attr_val) > 1:
            setattr(traffic_influ_data, 'temp_validities', attr_val)
        elif hasattr(traffic_influ_data, attr_name) and attr_val:
            setattr(traffic_influ_data, attr_name, attr_val)
    
    # if traffic_influ_sub.any_ue_ind:
    #     traffic_influ_data.inter_group_id = "AnyUE"
    if intGroupID:
        traffic_influ_data.inter_group_id = intGroupID
    elif supi:
        traffic_influ_data.supi = supi

    if traffic_influ_sub.subscribed_events and "UP_PATH_CHANGE" in traffic_influ_sub.subscribed_events:
        #map influ sub dest notif to an id and save
        traffic_influ_data.up_path_chg_notif_corre_id = 1 #test
        traffic_influ_data.up_path_chg_notif_uri = f"http://{conf.HOSTS['NEF']}:80/up_path_change"

    if traffic_influ_sub.temp_validities and len(traffic_influ_sub.temp_validities) == 1:
        traffic_influ_data.valid_start_time = traffic_influ_sub.temp_validities[0].start_time
        traffic_influ_data.valid_end_time = traffic_influ_sub.temp_validities[0].stop_time

    print("--------------------influ data-------------------")
    print(traffic_influ_data)
    async with httpx.AsyncClient(http1=False, http2=True) as client:
            response = await client.put(
                f"http://{conf.HOSTS['UDR'][0]}:7777/nudr-dr/v1/application-data/influenceData",
                headers={'Accept': 'application/json,application/problem+json'},
                data=json.dumps(traffic_influ_data.to_dict())
            )
            print(response.text)
            
    return response

# async def udr_app_data_update(sub: TrafficInfluSub):
#     traffic_influ_data = TrafficInfluData()
    
#     for attr_name in traffic_influ_sub.attribute_map.keys():
#         attr_val = getattr(traffic_influ_sub, attr_name)
#         if attr_name == 'tfcCorrInd':
#             setattr(traffic_influ_data, 'traff_corre_ind', attr_val)
#         elif attr_name == 'notificationDestination':
#             setattr(traffic_influ_data, 'up_path_chg_notif_uri', attr_val)
#         elif hasattr(traffic_influ_data, attr_name) and attr_val:
#             setattr(traffic_influ_data, attr_name, attr_val)
    
#     if traffic_influ_sub.any_ue_ind:
#         traffic_influ_data.inter_group_id = "AnyUE"
#     elif intGroupID:
#         traffic_influ_data.inter_group_id = intGroupID
#     elif supi:
#         traffic_influ_data.supi = supi

#     if len(traffic_influ_sub.temp_validities) == 1:
#         traffic_influ_data.valid_start_time = traffic_influ_sub.temp_validities[0].start_time
#         traffic_influ_data.valid_end_time = traffic_influ_sub.temp_validities[0].stop_time

async def udr_app_data_delete(sub: TrafficInfluSub):

    async with httpx.AsyncClient(http1=False, http2=True) as client:
            response = await client.delete(
                f"http://{conf.HOSTS['UDR'][0]}:7777/nudr-dr/v1/application-data/influenceData",
                headers={'Accept': 'application/json,application/problem+json'},
                data=json.dumps(sub.to_dict())
            )
            print(response.text)
            
    return response
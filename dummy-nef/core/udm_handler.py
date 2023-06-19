import httpx
import json
from api.config import conf
from session import db
from models.traffic_influ_sub import TrafficInfluSub
from models.pcf_binding import PcfBinding


async def udm_sdm_id_translation(ueId: str=None):
      
    async with httpx.AsyncClient(http1=False, http2=True) as client:
            response = await client.get(
                f"http://{conf.HOSTS['UDM'][0]}:7777/nudm_sdm/v1/{ueId}/id-translation-result",
                headers={'Accept': 'application/json,application/problem+json'}
            )
            print(response.text)

    return response

async def udm_sdm_group_identifiers_translation(ext_group_id: str=None):
    params = {'ext_group_id': ext_group_id}

    async with httpx.AsyncClient(http1=False, http2=True) as client:
            response = await client.get(
                f"http://{conf.HOSTS['UDM'][0]}:7777/nudm_sdm/v1/group-data/group-identifiers",
                headers={'Accept': 'application/json,application/problem+json'},
                params=params
            )
            print(response.text)

    return response
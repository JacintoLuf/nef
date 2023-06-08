import httpx
import json
from api.config import conf
from session import db
from models.traffic_influ_sub import TrafficInfluSub
from models.pcf_binding import PcfBinding

async def udm_sdm(sub: TrafficInfluSub) -> tuple[int, PcfBinding]:

    params = {'ipv4Addr': sub.ipv4_addr,
              'ipv6Addr': sub.ipv6_addr,
              'macAddr': sub.mac_addr,
              'gpsi': sub.gpsi,
              'dnn': sub.dnn,
              'snssai': sub.snssai}

    async with httpx.AsyncClient(http1=False, http2=True) as client:
            response = await client.get(
                "http://"+conf.HOSTS["UDM"][0]+":7777/nudm_sdm/v2/",
                headers={'Accept': 'application/json,application/problem+json'},
                params=params
            )
            print(response.text)
            if response.status_code is 204:
                  return (response.status_code, None)
            pcf_binding = PcfBinding.from_dict(response.json())


    return (response.status_code, pcf_binding)

async def udm_uecm_get_group_identifiers():
    async with httpx.AsyncClient(http1=False, http2=True) as client:
            response = await client.get(
                "http://"+conf.HOSTS["UDM"][0]+":7777/nudm_uecm/v1/group-data/group-identifiers",
                headers={'Accept': 'application/json,application/problem+json'}
            )
            print("-----------------------ids-----------------------")
            print(response.text)
            print("-------------------------------------------------")

    return response.status_code
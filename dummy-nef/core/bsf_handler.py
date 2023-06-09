import httpx
import json
from api.config import conf
from session import db
import core.udm_handler as udm_handler
from models.traffic_influ_sub import TrafficInfluSub
from models.pcf_binding import PcfBinding

async def bsf_management_discovery(sub: TrafficInfluSub=None) -> tuple[int, PcfBinding]:
    if not sub:
        return (400, None)
    elif sub.ipv4_addr:
        #supi = udm_handler.udm_sdm_id_trans(sub.gpsi)
        params = {'ipv4Addr': sub.ipv4_addr}
    elif sub.ipv6_addr:
        #supi = udm_handler.udm_sdm_id_trans(sub.gpsi)
        params = {'ipv6Prefix': sub.ipv6_addr}
    elif sub.mac_addr:
        #supi = udm_handler.udm_sdm_id_trans(sub.gpsi)
        params = {'macAddr48': sub.mac_addr}
    else:
        params = {'gpsi': sub.gpsi, 'dnn': sub.dnn, 'snssai': sub.snssai}

    async with httpx.AsyncClient(http1=False, http2=True) as client:
            response = await client.get(
                "http://"+conf.HOSTS["BSF"][0]+":7777/nbsf-management/v1/pcfBindings",
                headers={'Accept': 'application/json,application/problem+json'},
                params=params
            )
            print(response.text)
            if response.status_code != 200:
                  return (response.status_code, None)
            pcf_binding = PcfBinding.from_dict(response.json())


    return (response.status_code, pcf_binding)
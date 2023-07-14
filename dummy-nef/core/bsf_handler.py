import httpx
from api.config import conf
from models.traffic_influ_sub import TrafficInfluSub

async def bsf_management_discovery(sub: TrafficInfluSub=None):
    if sub.ipv4_addr:
        params = {'ipv4Addr': sub.ipv4_addr}
    elif sub.ipv6_addr:
        params = {'ipv6Prefix': sub.ipv6_addr}
    elif sub.mac_addr:
        params = {'macAddr48': sub.mac_addr}
    else:
        params = {'gpsi': sub.gpsi, 'dnn': sub.dnn, 'snssai': sub.snssai}
    print(conf.HOSTS['BSF'][0])
    async with httpx.AsyncClient(http1=False, http2=True) as client:
            response = await client.get(
                f"http://{conf.HOSTS['BSF'][0]}:7777/nbsf-management/v1/pcfBindings",
                headers={'Accept': 'application/json,application/problem+json'},
                params=params
            )

    return {'code': response.status_code, 'response': response.json()}
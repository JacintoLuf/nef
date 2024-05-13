import httpx
from api.config import conf

async def bsf_management_discovery(params):
    async with httpx.AsyncClient(http1=False, http2=True) as client:
            response = await client.get(
                url=f"http://{conf.HOSTS['BSF'][0]}/nbsf-management/v1/pcfBindings",
                headers={'Accept': 'application/json,application/problem+json'},
                params=params
            )
    res = response.json()
    return {'code': response.status_code, 'response': res}
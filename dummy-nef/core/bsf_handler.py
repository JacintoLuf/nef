import httpx
from api.config import conf

async def bsf_management_discovery(params):
    async with httpx.AsyncClient(http1=False, http2=True) as client:
            response = await client.get(
                url=f"http://{conf.HOSTS['BSF'][0]}:7777/nbsf-management/v1/pcfBindings",
                headers={'Accept': 'application/json,application/problem+json'},
                params=params
            )

    return {'code': response.status_code, 'response': response.json()}
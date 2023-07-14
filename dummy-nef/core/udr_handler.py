import httpx
import json
from api.config import conf
from models.traffic_influ_sub import TrafficInfluSub

async def udr_app_data_retrieval(loc: str=None):
    uri = loc or f"http://{conf.HOSTS['UDR'][0]}:7777/nudr-dr/v1/application-data/influenceData"
    #params = {'dnn': "", 'snssai': '', 'internal-Group-Id': '', 'supi': ''}
    async with httpx.AsyncClient(http1=False, http2=True) as client:
            response = await client.get(
                uri,
                headers={'Accept': 'application/json,application/problem+json'},
                #params=params
            )
            print(response.headers)
            print(response.text)

    return response.status_code

async def udr_app_data_insert(sub: TrafficInfluSub):

    async with httpx.AsyncClient(http1=False, http2=True) as client:
            response = await client.put(
                f"http://{conf.HOSTS['UDR'][0]}:7777/nudr-dr/v1/application-data/influenceData",
                headers={'Accept': 'application/json,application/problem+json'},
                data=json.dumps(sub.to_dict())
            )
            print(response.headers)
            print(response.text)
            
    return {'doc': response.json(), 'location': response.headers['location']}
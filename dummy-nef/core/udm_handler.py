import httpx
import json
from api.config import conf
from models.monitoring_event_subscription import MonitoringEventSubscription


async def udm_sdm_id_translation(ueId: str=None):
    async with httpx.AsyncClient(http1=False, http2=True) as client:
        response = await client.get(
            f"http://{conf.HOSTS['UDM'][0]}/nudm-sdm/v2/{ueId}/id-translation-result",
            headers={'Accept': 'application/json,application/problem+json'}
        )
        print(response.text)

    return response

async def udm_sdm_group_identifiers_translation(ext_group_id: str=None):
    params = {'ext_group_id': ext_group_id}

    async with httpx.AsyncClient(http1=False, http2=True) as client:
        response = await client.get(
            f"http://{conf.HOSTS['UDM'][0]}/nudm-sdm/v2/group-data/group-identifiers",
            headers={'Accept': 'application/json,application/problem+json'},
            params=params
        )
        print(response.text)

    return response

async def ee_subscription_create(monEvtSub: MonitoringEventSubscription):
    
    ueIdentity = "^anyUE$"
    ee_sub = ''
    async with httpx.AsyncClient(http1=False, http2=True) as client:
        response = await client.post(
            f"http://{conf.HOSTS['UDM'][0]}/nudm-ee/v1/{ueIdentity}/ee-subscriptions",
            headers={'Accept': 'application/json,application/problem+json'},
            params=json.dumps(ee_sub.to_dict())
        )
        print(response.text)

    return response
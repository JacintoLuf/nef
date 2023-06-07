import httpx
import json
from api.config import conf
from session import db
from models.traffic_influ_sub import TrafficInfluSub
from models.pcf_binding import PcfBinding

async def pcf_policy_authorization() -> int:

    async with httpx.AsyncClient(http1=False, http2=True) as client:
            response = await client.post(
                "http://"+conf.HOSTS["PCF"][0]+":7777/npcf-policyauthorization/v1//app-sessions",
                headers={'Accept': 'application/json,application/problem+json'}
            )
            print(response.text)

    return response.status_code

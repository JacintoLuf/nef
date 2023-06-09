import httpx
import json
from api.config import conf
from session import db

async def udr_data_retrieval() -> int:

    params = {}
    print("------------------------------subs data------------------------------")
    async with httpx.AsyncClient(http1=False, http2=True) as client:
            response = await client.get(
                "http://"+conf.HOSTS["UDR"][0]+":7777/nudr-dr/v1/subscription-data",
                headers={'Accept': 'application/json,application/problem+json'},
                params=params
            )
            print(response.text)
    print("------------------------------policy data------------------------------")
    async with httpx.AsyncClient(http1=False, http2=True) as client:
            response = await client.get(
                "http://"+conf.HOSTS["UDR"][0]+":7777/nudr-dr/v1/policy-data/bdt-data",
                headers={'Accept': 'application/json,application/problem+json'},
                params=params
            )
            print(response.text)
    print("------------------------------exposure data------------------------------")
    async with httpx.AsyncClient(http1=False, http2=True) as client:
            response = await client.get(
                "http://"+conf.HOSTS["UDR"][0]+":7777/nudr-dr/v1/exposure-data",
                headers={'Accept': 'application/json,application/problem+json'},
                params=params
            )
            print(response.text)
    print("------------------------------app data------------------------------")
    async with httpx.AsyncClient(http1=False, http2=True) as client:
            response = await client.get(
                "http://"+conf.HOSTS["UDR"][0]+":7777/nudr-dr/v1/application-data",
                headers={'Accept': 'application/json,application/problem+json'},
                params=params
            )
            print(response.text)

    return response.status_code
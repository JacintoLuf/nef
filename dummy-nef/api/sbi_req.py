import httpx
from config import conf
from fastapi import Request, Response, HTTPException

async def validate_req(request: Request):
    if request.headers['Accept'] not in conf.GLOBAL_HEADERS['Accept']:
        raise HTTPException(status_code=httpx.codes.NOT_ACCEPTABLE)
    return

async def get_req(url, headers=None, params=None):
    async with httpx.AsyncClient(http1=False, http2=True) as client:
        response = await client.get(
            url=url,
            headers=headers,
            params=params,
        )
        print(response.text)
    return response

async def post_req(url, headers=None, data=None):
    async with httpx.AsyncClient(http1=False, http2=True) as client:
        response = await client.post(
            url=url,
            headers=headers,
            data=data
        )
        print(response.text)
    return response

async def put_req(url, headers=None, data=None):
    async with httpx.AsyncClient(http1=False, http2=True) as client:
        response = await client.put(
            url=url,
            headers=headers,
            data=data
        )
        print(response.text)
    return response

async def patch_req(url, headers=None, data=None):
    async with httpx.AsyncClient(http1=False, http2=True) as client:
        response = await client.patch(
            url=url,
            headers=headers,
            data=data
        )
        print(response.text)
    return response


async def delete_req(url, headers=None, data=None):
    async with httpx.AsyncClient(http1=False, http2=True) as client:
        response = await client.delete(
            url=url,
            headers=headers,
        )
        print(response.text)
    return response

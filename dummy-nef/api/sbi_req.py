import httpx

async def get_req(url, headers=None):
    async with httpx.AsyncClient(http1=False, http2=True) as client:
        response = await client.get(
            url=url,
            headers=headers
        )
    return response

async def post_req(url, headers=None, data=None):
    async with httpx.AsyncClient(http1=False, http2=True) as client:
        response = await client.post(
            url=url,
            headers=headers,
            data=data
        )
    return response

async def put_req(url, headers=None, data=None):
    async with httpx.AsyncClient(http1=False, http2=True) as client:
        response = await client.put(
            url=url,
            headers=headers,
            data=data
        )
    return response

async def patch_req(url, headers=None, data=None):
    async with httpx.AsyncClient(http1=False, http2=True) as client:
        response = await client.patch(
            url=url,
            headers=headers,
            data=data
        )
    return response


async def delete_req(url, headers=None, data=None):
    async with httpx.AsyncClient(http1=False, http2=True) as client:
        response = await client.delete(
            url=url,
            headers=headers,
            data=data
        )
    return response

from typing import Union
from fastapi import FastAPI
import ssl
import http.client
import httpx
from httpx._config import SSLConfig

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/test")
async def test_conn():
    ctx = ssl.create_default_context()

    # Configure TLS 1.2 ciphersuites
    ctx.set_ciphers('ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES128-GCM-SHA256')
    ctx.options |= ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1 | ssl.OP_NO_TLSv1_3
    ctx.options |= ssl.OP_SINGLE_ECDH_USE
    ctx.options |= ssl.OP_NO_COMPRESSION
    ctx.set_alpn_protocols(["h2"])

    async with httpx.AsyncClient(http2=True, verify=False, ssl=ctx) as client:
        response = await client.get(
            "https://10.244.2.42/nnrf-nfm/v1/nf-instances",
            headers={'Accept': 'application/json,application/problem+json'}
        )
        print(response.text)
    return response.json()

@app.get("/test2")
def test_conn2():
    # set the TLS version to TLSv1.2
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)

    # set the cipher suites according to the recommended list
    context.set_ciphers('ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES128-GCM-SHA256:' \
                        'ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-AES256-GCM-SHA384:' \
                        'DHE-RSA-AES128-GCM-SHA256:DHE-DSS-AES128-GCM-SHA256:' \
                        'DHE-RSA-AES256-GCM-SHA384:DHE-DSS-AES256-GCM-SHA384')

    # disable SSLv2, SSLv3 and compression to prevent known attacks
    context.options |= ssl.OP_NO_SSLv2
    context.options |= ssl.OP_NO_SSLv3
    context.options |= ssl.OP_NO_COMPRESSION

    # load the trusted CA certificates
    context.load_verify_locations('cert.pem')

    # connect to the Open5GS NRF using HTTPS
    conn = http.client.HTTPSConnection('10.244.2.42', port=443, context=context)

    # send a GET request
    conn.request('GET', '/nnrf-nfm/v1/nf-instances', headers={'Accept': 'application/json'})

    # get the response
    res = conn.getresponse()
    data = res.read()

    # print the response
    return data.decode('utf-8')
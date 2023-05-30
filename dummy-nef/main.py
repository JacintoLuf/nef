from fastapi import FastAPI
from fastapi_utils.tasks import repeat_every
from session import async_db
import httpx
import logging
from api.config import conf
import core.nrf_handler as nrf_handler

app = FastAPI()
logger = logging.getLogger(__name__)


@app.on_event("startup")
async def startup():
    print("starting up")
    res = await nrf_handler.nrf_discovery()
    res = await nrf_handler.nf_register()
    if res == httpx.codes.CREATED:
        nrf_heartbeat()  
    print("started")

@repeat_every(seconds=conf.NEF_PROFILE.heart_beat_timer - 5)
async def nrf_heartbeat():
    await nrf_handler.nf_register_heart_beat()
    
@app.on_event("shutdown")
async def shutdown():
    print("shuting down...")
    nrf_handler.nf_deregister()

@app.get("/")
async def read_root():
    collection = async_db["nf_instances"]
    insts = []
    async for user in collection.find({}):
        insts.append(user)
    return {'nfs instances': str(insts)}



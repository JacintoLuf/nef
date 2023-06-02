#from models.traffic_influ_sub import TrafficInfluSub
from session import async_db as db


async def traffic_influence_subscription_get():
    collection = db["traffic_influ_sub"]
    return 1

async def traffic_influence_subscription_post():
    collection = db["traffic_influ_sub"]
    return 1


async def individual_traffic_influence_subscription_get():
    collection = db["traffic_influ_sub"]
    return 1

async def individual_traffic_influence_subscription_put():
    collection = db["traffic_influ_sub"]
    return 1

async def individual_traffic_influence_subscription_patch():
    collection = db["traffic_influ_sub"]
    return 1

async def individual_traffic_influence_subscription_delete():
    collection = db["traffic_influ_sub"]
    return 1
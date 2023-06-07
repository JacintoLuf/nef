from session import async_db as db
from models.traffic_influ_sub import TrafficInfluSub


async def traffic_influence_subscription_get(appId: str, subID: str=None):
    collection = db["traffic_influ_sub"]
    if not subID:
        docs = collection.find({'af_app_id': appId})
        if not docs:
            return 404
        return docs
    else:
        doc = collection.find({'af_app_id': appId, '_id': subID})
        if not doc:
            return 404
        return doc 
    return 200

async def traffic_influence_subscription_post(sub: TrafficInfluSub):
    collection = db["traffic_influ_sub"]
    try:
        result = collection.insert_one(sub)
        result.inserted_id
        return 201
    except:
        return 500


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
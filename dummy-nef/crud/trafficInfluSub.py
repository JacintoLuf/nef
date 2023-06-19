from session import async_db as db
from models.traffic_influ_sub import TrafficInfluSub


async def traffic_influence_subscription_get(appId: str, subId: str=None):
    collection = db["traffic_influ_sub"]
    if not subId:
        docs = collection.find({'af_service_id': appId})
        if not docs:
            return 404
        return docs
    else:
        docs = []
        for doc in collection.find_one({'af_service_id': appId, '_id': subId}):
            docs.append(doc)
        return docs
    return 200

async def traffic_influence_subscription_post(sub: TrafficInfluSub):
    collection = db["traffic_influ_sub"]
    try:
        result = collection.insert_one(sub)
        print(result.inserted_id)
        return result.inserted_id
    except:
        return 500

async def individual_traffic_influence_subscription_put():
    collection = db["traffic_influ_sub"]
    return 1

async def individual_traffic_influence_subscription_patch():
    collection = db["traffic_influ_sub"]
    return 1

async def individual_traffic_influence_subscription_delete(appId: str, subId: str=None):
    collection = db["traffic_influ_sub"]
    if appId and subId:
        reuslt = collection.delete_one({'af_service_id': appId, '_id': subId})
    return 1
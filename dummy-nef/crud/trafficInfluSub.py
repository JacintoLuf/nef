from secrets import token_bytes
from session import async_db as db
from models.traffic_influ_sub import TrafficInfluSub


async def traffic_influence_subscription_get(afId: str, subId: str=None):
    collection = db["traffic_influ_sub"]
    if not subId:
        doc = await collection.find_one({'_id': subId, 'sub': {'af_service_id': afId}})
        return doc
    else:
        docs = []
        for doc in await collection.find({'af_service_id': afId}):
            docs.append(doc)
        return docs or None

async def traffic_influence_subscription_post(sub: TrafficInfluSub):
    collection = db["traffic_influ_sub"]
    subId = '1' #token_bytes(16)
    document = {'_id': subId, 'sub': sub.to_dict}
    try:
        result = await collection.insert_one(document)
        print(result.inserted_id)
        return result.inserted_id
    except:
        return None

async def individual_traffic_influence_subscription_update():
    collection = db["traffic_influ_sub"]
    return 1

async def individual_traffic_influence_subscription_delete(afId: str, subId: str=None):
    collection = db["traffic_influ_sub"]
    if afId and subId:
        result = collection.delete_one({'_id': subId, 'sub': {'af_service_id': afId}})
    return result
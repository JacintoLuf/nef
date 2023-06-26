from secrets import token_bytes
from session import async_db as db
from models.traffic_influ_sub import TrafficInfluSub
from models.traffic_influ_sub_patch import TrafficInfluSubPatch


async def traffic_influence_subscription_get(afId: str, subId: str=None):
    collection = db["traffic_influ_sub"]
    if subId:
        doc = await collection.find_one({'_id': subId, 'sub': {'af_service_id': afId}})
        return doc
    else:
        docs = []
        for doc in await collection.find({'sub': {'af_service_id': afId}}):
            docs.append(doc)
        return docs or None

async def traffic_influence_subscription_post(sub: TrafficInfluSub, location: str):
    collection = db["traffic_influ_sub"]
    subId = '1' #token_bytes(16)
    document = {'_id': subId, 'sub': sub.to_dict(), 'location': location}
    try:
        result = await collection.insert_one(document)
        print(result.inserted_id)
        return result.inserted_id
    except:
        return None

async def individual_traffic_influence_subscription_update(afId: str, subId: str, sub, partial=False):
    collection = db["traffic_influ_sub"]
    if partial:
        doc = await collection.find_one({'_id': subId, 'sub': {'af_service_id': afId}})
        if not doc:
            return 404
        updated_sub = TrafficInfluSub.from_dict(doc['sub'])
        traffic_influ_sub = TrafficInfluSubPatch.from_dict(sub)
        for attr_name in traffic_influ_sub.attribute_map.keys():
            setattr(updated_sub, attr_name, getattr(traffic_influ_sub, attr_name))
        res = await collection.update_one({'_id': doc['_id']}, updated_sub)
    else:
        traffic_influ_sub = TrafficInfluSub.from_dict(sub)
        res = await collection.update_one(traffic_influ_sub)
    return 1

async def individual_traffic_influence_subscription_delete(afId: str, subId: str=None):
    collection = db["traffic_influ_sub"]
    if afId and subId:
        result = await collection.delete_one({'_id': subId, 'sub': {'af_service_id': afId}})
    return result
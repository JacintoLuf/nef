import uuid
from api.config import conf
from pymongo.errors import DuplicateKeyError
from session import async_db as db
from models.traffic_influ_sub import TrafficInfluSub
from models.traffic_influ_sub_patch import TrafficInfluSubPatch

async def traffic_influence_subscription_get(afId: str=None, subId: str=None):
    collection = db["traffic_influ_sub"]
    if afId and subId:
        doc = await collection.find_one({'_id': subId, 'afId': afId})
        return None if not doc else doc
    elif afId:
        docs = []
        async for doc in collection.find({'afId': afId}):
            docs.append(doc)
        return None if not docs else docs

async def traffic_influence_subscription_insert(afId: str, sub: TrafficInfluSub, location: str, _id: str=None):
    collection = db["traffic_influ_sub"]
    # subId = str(uuid.uuid4().hex)
    document = {'_id': _id, 'afId': afId, 'sub': sub.to_dict(), 'location': location}
    try:
        result = await collection.insert_one(document)
        conf.logger.info(result.inserted_id)
        return result.inserted_id
    except DuplicateKeyError as e:
        document['_id'] = str(uuid.uuid4().hex)
        result = await collection.insert_one(document)
        conf.logger.info(result.inserted_id)
        return result.inserted_id
    except Exception as e:
        conf.logger.error(e)
        return None
    
async def individual_traffic_influence_subscription_delete(afId: str, subId: str=None):
    collection = db["traffic_influ_sub"]
    n = await collection.count_documents({})
    if afId and subId:
        try:
            result = await collection.delete_one({'_id': subId, 'afId': afId})
            return n - await collection.count_documents({})
        except Exception as e:
            conf.logger.error(e)
            return None
    return None
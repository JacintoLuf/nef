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
    else:
        #------security breach-----------
        docs = []
        async for doc in collection.find({}):
            docs.append(doc)
        return None if not docs else docs

async def traffic_influence_subscription_insert(afId: str, sub: TrafficInfluSub, location: str):
    collection = db["traffic_influ_sub"]
    subId = str(uuid.uuid4().hex)
    document = {'_id': subId, 'afId': afId, 'sub': sub.to_dict(), 'location': location}
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

async def individual_traffic_influence_subscription_update(afId: str, subId: str, sub, partial=False):
    collection = db["traffic_influ_sub"]
    if partial:
        doc = await collection.find_one({'_id': subId, 'afId': afId})
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
    return res

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
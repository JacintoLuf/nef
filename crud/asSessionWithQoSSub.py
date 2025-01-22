import uuid
from api.config import conf
from pymongo.errors import DuplicateKeyError
from session import async_db as db
from models.as_session_with_qo_s_subscription import AsSessionWithQoSSubscription
from models.as_session_with_qo_s_subscription_patch import AsSessionWithQoSSubscriptionPatch


async def check_id(subId: str):
    collection = db["as_session_with_qos_sub"]
    exists = await collection.find_one({'_id': subId})
    return True if exists else False

async def as_session_with_qos_subscription_get(scsAsId: str=None, subId: str=None):
    collection = db["as_session_with_qos_sub"]
    if subId:
        doc = await collection.find_one({'_id': subId, 'scsAsId': scsAsId})
        return None if not doc else doc
    elif scsAsId:
        docs = []
        async for doc in collection.find({'scsAsId': scsAsId}):
            docs.append(doc)
        return None if not docs else docs
    else:
        #------security breach-----------
        docs = []
        async for doc in collection.find({}):
            docs.append(doc)
        return None if not docs else docs

async def as_session_with_qos_subscription_insert(scsAsId: str, sub: AsSessionWithQoSSubscription, location: str, _id: str=None):
    collection = db["as_session_with_qos_sub"]
    # subId = str(uuid.uuid4().hex)
    document = {'_id': _id, 'scsAsId': scsAsId, 'sub': sub.to_dict(), 'location': location}
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

async def as_session_with_qos_subscription_update(scsAsId: str, subId: str, sub, partial=False):
    collection = db["as_session_with_qos_sub"]
    if partial:
        doc = await collection.find_one({'_id': subId, 'scsAsId': scsAsId})
        if not doc:
            return 404
        updated_sub = AsSessionWithQoSSubscription.from_dict(doc['sub'])
        as_session_with_qos_sub = AsSessionWithQoSSubscriptionPatch.from_dict(sub)
        for attr_name in as_session_with_qos_sub.attribute_map.keys():
            setattr(updated_sub, attr_name, getattr(as_session_with_qos_sub, attr_name))
        res = await collection.update_one({'_id': doc['_id']}, updated_sub)
    else:
        as_session_with_qos_sub = AsSessionWithQoSSubscription.from_dict(sub)
        res = await collection.update_one(as_session_with_qos_sub)

async def as_session_with_qos_subscription_delete(scsAsId: str, subId: str=None):
    collection = db["as_session_with_qos_sub"]
    n = await collection.count_documents({})
    if scsAsId and subId:
        try:
            result = await collection.delete_one({'_id': subId, 'scsAsId': scsAsId})
            return n - await collection.count_documents({})
        except Exception as e:
            conf.logger.error(e)
            return None
    return None
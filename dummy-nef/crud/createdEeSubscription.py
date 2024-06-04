import uuid
from pymongo.errors import DuplicateKeyError
from session import async_db as db
from models.created_ee_subscription import CreatedEeSubscription


async def created_ee_subscriptionscription_get(subId: str=None):
    collection = db["created_ee_subscription"]
    if subId:
        doc = await collection.find_one({'_id': subId})
        return None if not doc else doc
    else:
        docs = []
        async for doc in collection.find({}):
            docs.append(doc)
        return None if not docs else docs

async def created_ee_subscriptionscription_insert(sub: CreatedEeSubscription, location: str):
    collection = db["created_ee_subscription"]
    subId = str(uuid.uuid4().hex)
    document = {'_id': subId, 'sub': sub.to_dict(), 'location': location}
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

async def created_ee_subscriptionscription_update(subId: str, sub: CreatedEeSubscription, partial=False):
    collection = db["created_ee_subscription"]
    if partial:
        doc = await collection.find_one({'_id': subId})
        if not doc:
            return -1
        updated_sub = CreatedEeSubscription.from_dict(doc['sub'])
        for attr_name in sub.attribute_map.keys():
            setattr(updated_sub, attr_name, getattr(sub, attr_name))
        res = await collection.update_one({'_id': subId}, updated_sub)
    else:
        res = await collection.update_one({'_id': subId}, sub)

async def created_ee_subscriptionscription_delete(subId: str=None):
    collection = db["created_ee_subscription"]
    n = await collection.count_documents({})
    try:
        result = await collection.delete_one({'_id': subId})
        return n - await collection.count_documents({})
    except Exception as e:
        conf.logger.error(e)
        return None
    return None
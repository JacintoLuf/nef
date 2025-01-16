import uuid
from api.config import conf
from pymongo.errors import DuplicateKeyError
from session import async_db as db
from models.amf_created_event_subscription import AmfCreatedEventSubscription


async def created_ee_subscriptionscription_get(subId: str=None):
    collection = db["amf_created_event_subscription"]
    if subId:
        doc = await collection.find_one({'_id': subId})
        return None if not doc else doc
    else:
        docs = []
        async for doc in collection.find({}):
            docs.append(doc)
        return None if not docs else docs

async def created_ee_subscriptionscription_insert(subId: str, sub: AmfCreatedEventSubscription):
    collection = db["amf_created_event_subscription"]
    document = {'_id': subId, 'sub': sub.to_dict()}
    try:
        result = await collection.insert_one(document)
        conf.logger.info(result.inserted_id)
        return result.inserted_id
    except DuplicateKeyError as e:
        conf.logger.info("Duplicated key")
        return -1
    except Exception as e:
        conf.logger.error(e)
        return None

async def created_ee_subscriptionscription_update(subId: str, sub: AmfCreatedEventSubscription, partial=False):
    collection = db["amf_created_event_subscription"]
    if partial:
        doc = await collection.find_one({'_id': subId})
        if not doc:
            return -1
        updated_sub = AmfCreatedEventSubscription.from_dict(doc['sub'])
        for attr_name in sub.attribute_map.keys():
            setattr(updated_sub, attr_name, getattr(sub, attr_name))
        res = await collection.update_one({'_id': subId}, updated_sub)
    else:
        res = await collection.update_one({'_id': subId}, sub)

async def created_ee_subscriptionscription_delete(subId: str=None):
    collection = db["amf_created_event_subscription"]
    n = await collection.count_documents({})
    try:
        result = await collection.delete_one({'_id': subId})
        return n - await collection.count_documents({})
    except Exception as e:
        conf.logger.error(e)
        return None
    return None
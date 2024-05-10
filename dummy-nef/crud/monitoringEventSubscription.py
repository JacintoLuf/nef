import uuid
from pymongo.errors import DuplicateKeyError
from session import async_db as db
from models.monitoring_event_subscription import MonitoringEventSubscription 


async def monitoring_event_subscriptionscription_get(scsAsId: str=None, subId: str=None):
    collection = db["monitoring_event_subscription"]
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

async def monitoring_event_subscriptionscription_insert(scsAsId: str, sub: MonitoringEventSubscription, location: str):
    collection = db["monitoring_event_subscription"]
    subId = str(uuid.uuid4().hex)
    document = {'_id': subId, 'scsAsId': scsAsId, 'sub': sub.to_dict(), 'location': location}
    try:
        result = await collection.insert_one(document)
        print(result.inserted_id)
        return result.inserted_id
    except DuplicateKeyError as e:
        document['_id'] = str(uuid.uuid4().hex)
        result = await collection.insert_one(document)
        print(result.inserted_id)
        return result.inserted_id
    except Exception as e:
        print(e)
        return None

async def monitoring_event_subscriptionscription_update(scsAsId: str, subId: str, sub, partial=False):
    collection = db["monitoring_event_subscription"]
    if partial:
        doc = await collection.find_one({'_id': subId, 'scsAsId': scsAsId})
        if not doc:
            return 404
        updated_sub = MonitoringEventSubscription.from_dict(doc['sub'])
        monitoring_event_subscription = MonitoringEventSubscription.from_dict(sub)
        for attr_name in monitoring_event_subscription.attribute_map.keys():
            setattr(updated_sub, attr_name, getattr(monitoring_event_subscription, attr_name))
        res = await collection.update_one({'_id': doc['_id']}, updated_sub)
    else:
        monitoring_event_subscription = MonitoringEventSubscription.from_dict(sub)
        res = await collection.update_one(monitoring_event_subscription)

async def monitoring_event_subscriptionscription_delete(scsAsId: str, subId: str=None):
    collection = db["monitoring_event_subscription"]
    n = await collection.count_documents({})
    if scsAsId and subId:
        try:
            result = await collection.delete_one({'_id': subId, 'scsAsId': scsAsId})
            return n - await collection.count_documents({})
        except Exception as e:
            print(e)
            return None
    return None
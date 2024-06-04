from pymongo.errors import DuplicateKeyError
from secrets import token_bytes
from session import async_db as db
from models.subscription_data import SubscriptionData


async def subscription_data_get():
    collection = db["subscription_data"]
    docs = []
    async for doc in collection.find({}):
        docs.append(doc)
    return docs or None

async def subscription_data_insert(sub: SubscriptionData, location: str):
    collection = db["subscription_data"]
    subId = token_bytes(16)
    document = {'_id': subId, 'sub': sub.to_dict(), 'location': location}
    try:
        result = await collection.insert_one(document)
        conf.logger.info(result.inserted_id)
        return result.inserted_id
    except DuplicateKeyError:
        conf.logger.info("duplicate key")
        return None
    except Exception as e:
        conf.logger.error(e)
        return None

async def subscription_data_delete(subId: str=None):
    collection = db["subscription_data"]
    n = await collection.count_documents({})
    try:
        result = await collection.delete_one({'_id': subId})
        return n - await collection.count_documents({})
    except Exception as e:
        conf.logger.error(e)
        return -1
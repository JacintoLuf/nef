from pymongo import UpdateOne
from pymongo.errors import DuplicateKeyError
from session import async_db

async def get_one(nfId: str):
    collection = async_db["nf_instances"]
    doc = await collection.find_one({'_id': nfId})
    return doc

async def get_by_type(type: str):
    docs = []
    collection = async_db["nf_instances"]
    cursor = await collection.find({'profile': {'nfType': type}})
    for doc in await cursor.to_list(length=100):
        docs.append(doc)
    return docs

async def get_all():
    docs = []
    collection = async_db["nf_instances"]
    async for doc in collection.find({}):
        docs.append(doc['profile'])
    return docs

async def insert_one(profile):
    collection = async_db["nf_instances"]
    query = {'_id': profile['nfInstanceId']}
    update = {"$set": {'profile': profile}}
    try:
        result = await collection.update_one(query, update, upsert=True)
        return result.modified_count or result.upserted_id
    except DuplicateKeyError:
        conf.logger.info("duplicate key")
        return None
    except Exception as e:
        conf.logger.error(e)
        return None

async def insert_many(profiles):
    collection = async_db["nf_instances"]
    try:
        bulk_operations = []
        for profile in profiles:
            query = {"_id": profile['nfInstanceId']}
            update = {"$set": {'profile': profile}}
            bulk_operations.append(UpdateOne(query, update, upsert=True))

        # Perform the bulk write operation
        result = await collection.bulk_write(bulk_operations)
        conf.logger.info(result)
        return result.modified_count + len(result.upserted_ids)
    except DuplicateKeyError:
        conf.logger.info("duplicate key")
        return None
    except Exception as e:
        conf.logger.error(e)
        return 0

async def update(profile):
    collection = async_db["nf_instances"]
    old_document = await collection.find_one({'_id': profile["nfInstanceId"]})
    if not old_document:
        return None
    _id = old_document['_id']
    try:
        result = await collection.replace_one({'_id': _id}, {'profile': profile})
        return result.modified_count
    except Exception as e:
        conf.logger.error(e)
        return -1

async def delete_one(profile):
    collection = async_db["nf_instances"]
    n = await collection.count_documents({})
    try:
        result = await collection.delete_one({'_id': profile['nfInstanceId']})
        return n - await collection.count_documents({})
    except Exception as e:
        conf.logger.error(e)
        return -1

async def delete_many(profiles):
    collection = async_db["nf_instances"]
    n = await collection.count_documents({})
    try:
        result = await collection.delete_one({'_id': {'$in': [profile['nfInstanceId'] for profile in profiles]}})
        return n - await collection.count_documents({})
    except Exception as e:
        conf.logger.error(e)
        return -1
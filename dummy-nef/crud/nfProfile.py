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
    collection = async_db["nf_instances2"]
    print("here")
    for doc in await collection.find({}):
        docs.append(doc)
    return docs

async def insert_one(profile):
    collection = async_db["nf_instances2"]
    doc = {'_id': profile['nfInstanceId'], 'profile': profile}
    update = {"$set": {'profile': doc}}
    try:
        result = await collection.update_one({"_id": profile['nfInstanceId']}, update, upsert=True)
        return result.modified_count
    except DuplicateKeyError:
        print("duplicate key")
        return None
    except Exception as e:
        print(e)
        return None

async def insert_many(profiles):
    collection = async_db["nf_instances"]
    docs = [{'_id': i['nfInstanceId'], 'profile': i} for i in profiles]
    try:
        result = await collection.insert_many(docs, { 'ordered': False })
        return result.inserted_ids
    except Exception as e:
        print(e)
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
        print(e)
        return -1

async def delete_one(profile):
    collection = async_db["nf_instances"]
    n = await collection.count_documents({})
    try:
        result = await collection.delete_one({'_id': profile['nfInstanceId']})
        return n - await collection.count_documents({})
    except Exception as e:
        print(e)
        return -1

async def delete_many(profiles):
    collection = async_db["nf_instances"]
    n = await collection.count_documents({})
    try:
        result = await collection.delete_one({'_id': {'$in': [profile['nfInstanceId'] for profile in profiles]}})
        return n - await collection.count_documents({})
    except Exception as e:
        print(e)
        return -1
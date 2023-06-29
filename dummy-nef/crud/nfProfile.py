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
    print("here")
    async for doc in await collection.find({}):
        docs.append(doc)
    print(docs)
    return docs

async def insert_one(profile):
    collection = async_db["nf_instances"]
    doc = {'_id': profile['nfInstanceId'], 'profile': profile}
    update = {"$set": {'profile': doc}}
    try:
        result = await collection.update_one({"_id": profile['nfInstanceId']}, update, upsert=True)
        return result.modified_count
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
    # coll = db.test_collection
    # old_document = await coll.find_one({'i': 50})
    # print('found document: %s' % pprint.pformat(old_document))
    # _id = old_document['_id']
    # result = await coll.replace_one({'_id': _id}, {'key': 'value'})
    # print('replaced %s document' % result.modified_count)
    # new_document = await coll.find_one({'_id': _id})
    # print('document is now %s' % pprint.pformat(new_document))

    #-------------------------

    # coll = db.test_collection
    # result = await coll.update_one({'i': 51}, {'$set': {'key': 'value'}})
    # print('updated %s document' % result.modified_count)
    # new_document = await coll.find_one({'i': 51})
    # print('document is now %s' % pprint.pformat(new_document))
    return 1

async def delete_one(profile):

    return 1

async def delete_many(profiles):

    return 1
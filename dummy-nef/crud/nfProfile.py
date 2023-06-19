from models.nf_profile import NFProfile
from session import async_db

async def insert_one(profile: NFProfile=None):
    collection = async_db["nf_instances"]
    criteria = {'nf_instance_id': profile.nf_instance_id}
    try:
        result = collection.update_one(profile)
        print(result.inserted_id)
    except Exception as e:
        print(e)
        return 0
    
    return 1

async def insert_many(profiles):
    collection = async_db["nf_instances"]
    
    try:
        result = collection.insert_many(profiles)
        result.inserted_ids
    except Exception as e:
        print(e)
        return 0
    
    return 1

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
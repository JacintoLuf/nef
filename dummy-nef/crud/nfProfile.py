from models.nf_profile import NFProfile
from session import async_db

async def insert_one(profile):
    collection = async_db["nf_instances"]

    try:
        result = collection.insert_one(profile)
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
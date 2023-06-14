from models.app_session_context import AppSessionContext
from session import async_db

async def get_one():
    collection = async_db["app_session_context"]

    result = collection.find({})

    return result

async def insert_one(context):
    collection = async_db["app_session_context"]

    try:
        result = collection.insert_one(context)
        print(result.inserted_id)
    except Exception as e:
        print(e)
        return 0
    
    return 1
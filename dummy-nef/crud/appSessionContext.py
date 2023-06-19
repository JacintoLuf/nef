from models.app_session_context import AppSessionContext
from session import async_db

async def get_one(afId: str=None):
    if not afId:
        return None
    collection = async_db["app_session_context"]

    result = collection.find({})
    app_session_context = AppSessionContext.from_dict(result)

    return app_session_context

async def insert_one(context):
    collection = async_db["app_session_context"]

    try:
        result = collection.insert_one(context)
        print(result.inserted_id)
    except Exception as e:
        print(e)
        return 0
    
    return 1
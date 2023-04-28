from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient
from api.config import config

conn = MongoClient(config.MONGO_URI)
async_conn = AsyncIOMotorClient(config.MONGO_URI)
async_client = async_conn["nef"]
static_client = conn["nef"]

#client = MongoClient(settings.MONGO_URL, username=settings.MONGO_USER, password=settings.MONGO_PASS)

def close():
    for collection in async_conn.list_collection_names():
        async_conn.drop_collection(collection)
    print("Database reset complete.")
    async_conn.close()
    conn.close()

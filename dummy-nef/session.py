from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient
from api.config import conf

client = MongoClient(conf.MONGO_URI)
async_client = AsyncIOMotorClient(conf.MONGO_URI)
async_db = async_client["nef"]
db = client["nef"]

#client = MongoClient(settings.MONGO_URL, username=settings.MONGO_USER, password=settings.MONGO_PASS)

def close():
    for collection in async_client.list_collection_names():
        async_client.drop_collection(collection)
    print("Database reset complete.")
    async_client.close()
    client.close()

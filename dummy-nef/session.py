from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient
from api.config import conf

client = MongoClient(conf.NF_IP["MONGODB"], username='root', password='password')
async_client = AsyncIOMotorClient(conf.MONGO_URI,username='root',password='password')
async_db = async_client["nef"]
db = client["nef"]

def close():
    for collection in async_client.list_collection_names():
        async_client.drop_collection(collection)
    print("Database reset complete.")
    async_client.close()
    client.close()

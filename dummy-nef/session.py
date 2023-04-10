from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient
from api.config import settings

db_client = AsyncIOMotorClient(settings.MONGO_URI)
#client = MongoClient(settings.MONGO_URL, username=settings.MONGO_USER, password=settings.MONGO_PASS)

def close():
    client.close()

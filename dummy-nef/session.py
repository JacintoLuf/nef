from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient
from api.config import conf

#client = MongoClient(conf.HOSTS["MONGODB"], username='root', password='lKiOIOTwtJ')
#async_client = AsyncIOMotorClient(conf.MONGO_URI,username='root',password='lKiOIOTwtJ')
client = MongoClient(conf.HOSTS["MONGODB"])
async_client = AsyncIOMotorClient(conf.MONGO_URI)
async_db = async_client["nef"]
db = client["nef"]

def clean_db():
    collections = ['traffic_influ_sub', 'as_session_with_qos_sub']
    try:
        for i in collections:
            print(f"cleaning {i} collection docs")
            async_db[i].delete_many({})
        print("Database cleaned.")
        return True
    except Exception as e:
        print("Error cleaning database!")
        return False

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
    collections = ['nf_instances', 'traffic_influ_sub', 'as_session_with_qos_sub', 'subscription_data', ]
    try:
        for i in collections:
            conf.logger.info(f"cleaning {i} collection docs")
            async_db[i].delete_many({})
        conf.logger.info("Database cleaned.")
        return True
    except Exception as e:
        conf.logger.info("Error cleaning database!")
        return False

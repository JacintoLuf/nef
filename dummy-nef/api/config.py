import os
import uuid

class Settings():
    MONGO_IP = os.getenv('MONGO_IP') or os.getenv('NEF-MONGODB-HOST') or "10.99.149.247"
    if os.getenv('NEF-MONGODB-SERVICE-HOST') is None:
        print("no kube mongo host")
        MONGO_IP = "10.99.149.247"  #10.99.149.247
    MONGO_URI = "mongodb://"+MONGO_IP+"/nef"  
    #MONGO_URI = "mongodb://root:pass@nef-mongodb.open5gs.svc.cluster.local:27017/admin?authSource=admin"
    FIRST_SUPERUSER = "admin@it.av.pt"
    FIRST_SUPERUSER_PASSWORD = "1234"

    API_UUID = uuid.uuid4()
    
    NRF_IP = os.getenv('NRF_IP')+":7777" or os.getenv('OPEN5GS-NRF-SBI-HOST')+":7777"
    AMF_IP = os.getenv('AMF_IP')+":7777" or os.getenv('OPEN5GS-AMF-SBI-HOST')+":7777"
    SMF_IP = os.getenv('SMF_IP')+":7777" or os.getenv('OPEN5GS-SMF-SBI-HOST')+":7777"


config = Settings()
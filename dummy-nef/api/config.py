import os
import uuid

class Settings():
    if os.getenv('MONGO_IP') is not None:
        MONGO_IP = os.getenv('MONGO_IP')
    elif os.getenv('NEF-MONGODB-HOST') is not None:
        MONGO_IP = os.getenv('NEF-MONGODB-HOST')
    else:
        MONGO_IP = "10.99.149.247"
    print("mongo ip: "+MONGO_IP)
    MONGO_URI = "mongodb://"+MONGO_IP+"/nef"    #MONGO_URI = "mongodb://root:pass@nef-mongodb.open5gs.svc.cluster.local:27017/admin?authSource=admin"
    FIRST_SUPERUSER = "admin@it.av.pt"
    FIRST_SUPERUSER_PASSWORD = "1234"

    API_UUID = str(uuid.uuid4())
    
    if os.getenv('NRF_IP') is not None and os.getenv('AMF_IP')  is not None and os.getenv('SMF_IP') is not None:
        NRF_IP = os.getenv('NRF_IP')+":7777"
        AMF_IP = os.getenv('AMF_IP')+":7777"
        SMF_IP = os.getenv('SMF_IP')+":7777"
    elif os.getenv('OPEN5GS-NRF-SBI-HOST') is not None and os.getenv('OPEN5GS-AMF-SBI-HOST') is not None and os.getenv('OPEN5GS-SMF-SBI-HOST') is not None:
        NRF_IP = os.getenv('OPEN5GS-NRF-SBI-HOST')+":7777"
        AMF_IP = os.getenv('OPEN5GS-AMF-SBI-HOST')+":7777"
        SMF_IP = os.getenv('OPEN5GS-SMF-SBI-HOST')+":7777"
    else:
        NRF_IP = "10.103.218.237:7777"
        AMF_IP = "10.102.17.49:7777"
        SMF_IP = "10.111.153.168:80"

        
config = Settings()
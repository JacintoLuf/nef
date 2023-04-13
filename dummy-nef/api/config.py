import uuid

class Settings():
    MONGO_URI = "mongodb://root:pass@nef-mongodb.open5gs.svc.cluster.local:27017/admin?authSource=admin"
    MONGO_USER = "root"
    MONGO_PASS = "pass"
    FIRST_SUPERUSER = "admin@it.av.pt"
    FIRST_SUPERUSER_PASSWORD = "1234"

    API_UUID = uuid.uuid4()
    
    # def gen_uuid():
    #     API_UUID = uuid.uuid4()


settings = Settings()
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
#from pymongo import MongoClient
from api.config import settings

#Create a db URL for SQLAlchemy in core/config.py/ Settings class
engine = create_engine(settings.MONGO_URL, pool_pre_ping=True, pool_size=150, max_overflow=20)
#Each instance is a db session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


#client = MongoClient(settings.MONGO_URL, username=settings.MONGO_USER, password=settings.MONGO_PASS)

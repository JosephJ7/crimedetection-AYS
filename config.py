from pymongo import MongoClient
from sqlalchemy import create_engine

''' This file must not be deployed for production but released for eduction purpose Only. '''

# MongoDB connection 
MONGO_URI = "mongodb+srv://josephjacobie2001:Demoadvp@advp.xqmcaw4.mongodb.net/" 
mongo_client = MongoClient(MONGO_URI)
mongo_db = mongo_client["Group_D"]


# PostgreSQL connection string
PG_CONN_STRING = "postgresql://user:password@localhost:5432/food_waste"
pg_engine = create_engine(PG_CONN_STRING)
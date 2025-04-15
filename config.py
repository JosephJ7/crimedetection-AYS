from pymongo import MongoClient
from sqlalchemy import create_engine

''' This file must not be deployed for production but released for eduction purpose Only. '''

# MongoDB connection 
MONGO_URI = "mongodb+srv://josephjacobie2001:Demoadvp@advp.xqmcaw4.mongodb.net/" 
mongo_client = MongoClient(MONGO_URI)
mongo_db = mongo_client["Group_D"]


# PostgreSQL connection string
PG_CONN_STRING = "postgresql://postgres:admin@localhost:5432/Group_D"
pg_engine = create_engine(PG_CONN_STRING)
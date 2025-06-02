
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

uri = "mongodb+srv://alessia00m:Password1234@cluster0.7if8c41.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)


#creo il db

db = client.unina

professors = db.professors

import datetime

moscatoDocument = {
    "name": {"first": "Vincenzo", "last": "Moscato"},
    "birth": datetime.datetime(1991, 6, 23),
    "death": datetime.datetime(2200, 6, 7),
    "courses": ["Big Data Engineering", "Machine Learning"]
}

professors.insert_one(moscatoDocument)

dbs = client.list_database_names()
collections = db.list_collection_names()
print(dbs)
print(collections)


def insert_test_doc():
    collection = db.unina #accedo alla collection
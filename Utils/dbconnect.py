from mongoengine import connect
from pymongo import MongoClient

# Establish a connection to MongoDB
client = MongoClient('mongodb://localhost:27017')

# Get the list of database names
database_names = client.list_database_names()

# Print the database names
for db_name in database_names:
    print(db_name)


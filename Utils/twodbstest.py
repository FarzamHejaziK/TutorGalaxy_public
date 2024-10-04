from pymongo import MongoClient
from flask import Flask
from database_init import db, User, Topic, TopicList
from mongoengine import disconnect

# Establish a connection to MongoDB
client = MongoClient('mongodb://localhost:27017')

# Print server version
print("MongoDB server version:", client.server_info()['version'])

# Print the list of databases
print("\nDatabases:", client.list_database_names())

# Access the 'newdb1' database
db1 = client['newdb1']

print("\nDocument counts in 'newdb1':")
for collection_name in ['users', 'topic_lists']:
    print(f"{collection_name}: {db1[collection_name].count_documents({})}")

# Create a new database 'newdb2' with the same collections as 'newdb1'
db2 = client['newdb2']

print("\nDocument counts in 'newdb2':")
for collection_name in ['users', 'topic_lists']:
    print(f"{collection_name}: {db2[collection_name].count_documents({})}")

app = Flask(__name__)
app.config['MONGODB_SETTINGS'] = {
    'db': 'newdb1',
    'host': 'localhost',
    'port': 27017
}

disconnect(alias='default')
db.init_app(app)

with app.app_context():
    # Print connection details
    print("\nFlask app database connection details:", db.connection)

    print("\nDefault database in Flask app:", db.get_db())

    # Fetch all users from the database
    users = User.objects.all()

    for user in users:
        print("\nUser email = ", user.email)

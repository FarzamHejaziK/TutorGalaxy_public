from flask import Flask
from flask_mongoengine import MongoEngine
from flask_login import UserMixin

app = Flask(__name__)
app.config['MONGODB_SETTINGS'] = {
    'db': 'newdb1',
    'host': 'localhost',
    'port': 27017
}
db = MongoEngine(app)

class Topic(db.EmbeddedDocument):
    user = db.ReferenceField('User')  # replace User with 'User'
    name = db.StringField(max_length=100)  # remove 'unique=True'
    goal = db.StringField()
    chatstarter = db.StringField()
    chat = db.StringField()  
    state = db.IntField()
    user_messages = db.ListField(db.StringField())
    system_messages = db.ListField(db.StringField())
    conversation_history = db.ListField(db.StringField())
    summary = db.StringField()
    message_queue = db.ListField(db.StringField())

class ConvCreator(db.EmbeddedDocument):
    user = db.ReferenceField('User')  # replace User with 'User'
    user_messages = db.ListField(db.StringField())
    system_messages = db.ListField(db.StringField())
    conversation_history = db.ListField(db.StringField())
    summary = db.StringField()
    message_queue = db.ListField(db.StringField())
    discussion = db.StringField()

class CreatedTopics(db.EmbeddedDocument):
    Topic = db.StringField()
    Goal = db.StringField()

class User(UserMixin, db.Document):
    email = db.StringField(max_length=100, unique=True)
    topics = db.ListField(db.EmbeddedDocumentField(Topic))
    conversations = db.ListField(db.EmbeddedDocumentField(ConvCreator)) 
    created_topics = db.ListField(db.EmbeddedDocumentField(CreatedTopics))


class TopicList(db.Document):
    topics = db.ListField(db.StringField())

from database_init import db, User, Topic, TopicList
from flask import Flask
from mongoengine import disconnect

## user and topic

app = Flask(__name__)
disconnect(alias='default')
db.init_app(app)

# Fetch all users from the database
users = User.objects.all()

for user in users:
    print(user.email)
    for topic in user.topics:
        print("topic = ",topic.name)
        print("goal = ",topic.goal)
        print("chat starter = ",topic.chatstarter)
        print("chat =",topic.chat )
        


'''for user in users:
    print(user.email)

    # Set topics and created_topics to empty lists and save
    user.topics = []
    user.created_topics = []
    user.save()

for user in users:
    print(user.email)
    for topic in user.created_topics:
        print("topic = ",topic.Topic)
        print("goal = ",topic.Goal)
'''        



# Confirm deletion
remaining_users = User.objects.count()
print(f"Remaining users: {remaining_users}")

'''
## Checking content of dB
app = Flask(__name__)
disconnect(alias='default')
db.init_app(app)

# Fetch all users from the database
users = User.objects.all()
topiclist = TopicList.objects.all() 

# Loop through each user
for user in users:
    print(f"User ID: {user.id}")
    
    # Loop through each topic for the user
    for topic in user.topics:
        print(f"  Topic name: {topic.name}")
        print(f"  State: {topic.state}")
        print(f"  User messages: {topic.user_messages}")
        print(f"  System messages: {topic.system_messages}")
        print(f"  Message queue: {topic.message_queue}")
        print(f"  Summary: {topic.summary}")
        print(f"  Conversation History: {topic.conversation_history}")

print(f"topics lsit :{topiclist}")
'''
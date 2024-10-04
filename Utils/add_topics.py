from database_init import db, User, Topic, TopicList
from flask import Flask
from mongoengine import disconnect

def add_topic(topic_name):
    # Retrieve the TopicList document
    topic_list = TopicList.objects.first()

    # Check if the topic_list is None
    if topic_list is None:
        # Create a new TopicList document
        topic_list = TopicList()
        topic_list.save()

    # Check if the topic is already in the list
    if topic_name not in topic_list.topics:
        # Add the topic to the list and save the document
        topic_list.topics.append(topic_name)
        topic_list.save()

        # Add the topic to the available_topics list for each user
        for user in User.objects.all():
            if topic_name not in user.taken_topics:
                user.available_topics.append(topic_name)
                user.save()


if __name__ == "__main__":
    topics_to_add = ["python", "C++", "PHP", "Java"]
    for topic in topics_to_add:
        add_topic(topic)
    topiclist = TopicList.objects.first()
    print(f"topics list: {topiclist.topics}")

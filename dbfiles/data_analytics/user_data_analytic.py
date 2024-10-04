import boto3
from ...config import *

# Scan users from the user_table
users = user_table.scan()['Items']

# Sort the users by the number of created topics in descending order
sorted_users = sorted(users, key=lambda x: len(x['created_topics']), reverse=True)

# Print the sorted users and their topics in a formatted way
total_users = 0

for user in sorted_users:
    email = user['email']
    created_topic_ids = user['created_topics']
    if created_topic_ids: 
        total_users += 1
        print(f"Email: {email}, Created Topics: {len(created_topic_ids)}")

        # Retrieve and sort the topics based on the number of messages
        topics_with_message_counts = []
        for topic_id in created_topic_ids:
            # Query the Topics_table to get the topic by userId and topicId
            response = Topics_table.get_item(
                Key={
                    'userId': email,
                    'topics_id': topic_id,
                }
                )
            # Assuming each topic only has one item in the response
            if response['Item']:
                topic_item = response['Item']
                message_count = len(topic_item.get('messages', []))
                topics_with_message_counts.append((topic_id, message_count))

        # Sort the topics by the number of messages in descending order
        sorted_topics = sorted(topics_with_message_counts, key=lambda x: x[1], reverse=True)

        # Print the topics and their message counts
        for topic_id, message_count in sorted_topics:
            print(f" - {topic_id} number_of_messages: {message_count}")
        print("\n")

print(f"Total users: {total_users}")

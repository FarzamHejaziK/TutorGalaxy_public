from flask import Flask, redirect, url_for, request, jsonify, stream_with_context, Blueprint
from tutor_agent.Conv_handler_improved_mem import TeachingAssistant_stream
from auth2 import auth, max_topic_messages_WO_sub, max_topic_topics_WO_sub #, blueprint
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
import os
from flask import render_template, make_response, stream_with_context, Response
from dotenv import load_dotenv
import time
from init_agent.Conv_Creator_basics import ConvCreator_stream
from config import *
from flask_cors import CORS
from datetime import timedelta
from code_excecution.code_execute import code_execution
from payment.stripe_subscription import payments_blueprint
from APIs.new_conv_public_apis import public_blueprint 
from text_to_speech.TTS import TTS_blueprint
import random
import sys
from boto3.dynamodb.types import TypeDeserializer

deserializer = TypeDeserializer()

tutor_history_blueprint = Blueprint('tutor_history', __name__)

# Function to chunk topic keys into batches of 100
def chunked_topic_keys(topic_keys, chunk_size=100):
    for i in range(0, len(topic_keys), chunk_size):
        yield topic_keys[i:i + chunk_size]

# Function to process batches and return deserialized topics
def get_deserialized_topics_for_batches(dynamodb_client, table_name, all_topic_keys):
    # Create a mapping of topic keys to their original indexes
    key_to_index = {str(key['topics_id']['S']): index for index, key in enumerate(all_topic_keys)}
    
    # Initialize a list with placeholders for all deserialized topics
    ordered_deserialized_topics = [None] * len(all_topic_keys)

    for topic_keys_chunk in chunked_topic_keys(all_topic_keys):
        batch_get_request = {
                table_name: {
                    'Keys': topic_keys_chunk,
                }
        }
        response = dynamodb_client.batch_get_item(RequestItems=batch_get_request)

        # Check for unprocessed keys in case of throttling or other issues and retry as needed
        while response.get('UnprocessedKeys', {}):
            response = dynamodb_client.batch_get_item(RequestItems=response['UnprocessedKeys'])

        # Deserialize the topics from the response for the current chunk
        for topic in response['Responses'][table_name]:
            deserialized_topic = {k: deserializer.deserialize(v) for k, v in topic.items()}
            original_index = key_to_index[str(deserialized_topic['topics_id'])]
            ordered_deserialized_topics[original_index] = deserialized_topic
    
    return ordered_deserialized_topics




@tutor_history_blueprint.route('/api/v1/user_profile', methods=['GET'])
def get_user_profile():
    current_user_email = get_jwt_identity()
    response = user_table.get_item(Key={'email': current_user_email})
    if 'Item' not in response:
        return jsonify({"error": "User not found"}), 404

    user = response['Item']
    subscribed = user.get('subscribed', {}).get('state', False)
    user_create_topic_permission = True
    if not subscribed:
        if len(user['created_topics']) >= max_topic_topics_WO_sub:
            user_create_topic_permission = False


    if user['created_topics']:
        topics_goals = []
        icons = asset_table.get_item(
            Key={
                    'asset_name': 'icon',  # replace with your userId
                })['Item']
        # Assuming you have a list of topic_ids and the current_user_email
        # Assuming 'user['created_topics']' is a list of topic IDs (strings) and 'current_user_email' is a string


        topic_keys = [
            {
                'userId': {'S': current_user_email},
                'topics_id': {'S': topic_id}
            } for topic_id in user['created_topics']
        ]

        topics = get_deserialized_topics_for_batches(dynamodb_client, Topics_table.name, topic_keys)[::-1]

        topics_goals = []
        for topic in topics:
            # Here, process each topic to structure it as needed for your response
            # This is where you would apply your existing logic to structure the topic data
            langid = topic.get('langid', "-1")
            langname = topic.get('lang_name', "-1")
            monaconame = topic.get('monaco_name', "-1")
            category = topic.get('category', "1") 
            if category not in ['1','2','3','4']: category = '1'
            

            current_topic= {
                'topic': topic['topic'],
                'goal': topic['goal'],
                'id': topic['topics_id'],
                'state': topic['state'],
                'lang_id': str(langid),
                'lang_name' : str(langname),
                'monaco_name': monaconame, 
                'create_topic_permission': user_create_topic_permission,
                'icon' : icons.get(category, icons['1']),
            }
            topics_goals.append(current_topic)
        return make_response(jsonify(topics_goals), 200)
    else:
        return jsonify({"error": "No topics found for the user"}), 404
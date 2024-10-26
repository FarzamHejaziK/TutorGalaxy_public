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

chat_history_blueprint = Blueprint('chat_history', __name__)

def chunked_message_keys(message_keys, chunk_size=100):
    for i in range(0, len(message_keys), chunk_size):
        yield message_keys[i:i + chunk_size]

# Function to process batches and return deserialized topics
def get_deserialized_message_for_batches(dynamodb_client, table_name, all_message_keys):
    key_to_index = {str(key['message_id']['S']): index for index, key in enumerate(all_message_keys)}
    
    # Initialize a list with placeholders for all deserialized topics
    ordered_deserialized_messages = [None] * len(all_message_keys)
    for message_keys_chunk in chunked_message_keys(all_message_keys):
        batch_get_request = {
                table_name: {
                    'Keys': message_keys_chunk,
                }
        }
        response = dynamodb_client.batch_get_item(RequestItems=batch_get_request)

        # Check for unprocessed keys in case of throttling or other issues and retry as needed
        while response.get('UnprocessedKeys', {}):
            response = dynamodb_client.batch_get_item(RequestItems=response['UnprocessedKeys'])

        # Deserialize the topics from the response for the current chunk
        for message in response['Responses'][table_name]:
            deserialized_message = {k: deserializer.deserialize(v) for k, v in message.items()}
            original_index = key_to_index[str(deserialized_message['message_id'])]
            ordered_deserialized_messages[original_index] = deserialized_message['message']
    
    return ordered_deserialized_messages

@chat_history_blueprint.route('/api/v1/chat_history', methods=['POST'])
def get_chat_history():
    current_user_email = get_jwt_identity()
    data = request.get_json()
    response = user_table.get_item(Key={'email': current_user_email})
    if 'Item' not in response:
        return jsonify({"error": "User not found"}), 404
    user = response['Item']
    topic_id = data.get('id')
    try:
        response = Topics_table.get_item(
            Key={
                'userId': current_user_email,  # replace with your userId
                'topics_id': topic_id  # replace with your topicId
            }
        )
    except Exception as e:
        return jsonify({"error": f"Error getting topic: {e}"}), 500

    if 'Item' not in response:
        return jsonify({"error": "Topic not found"}), 404

    topic = response['Item']
    topic_topic = topic['topic']
    topic_goal = topic['goal']
    topic_state = topic['state']
    topic_langid = topic.get('langid', "-1")
    topic_langname = topic.get('lang_name', "-1")
    topic_monaconame = topic.get('monaco_name', "-1")

    message_keys = [
            {
                'topics_id': {'S' : topic_id},
                'message_id': { 'S' :message_id},
            } for message_id in topic['messages']
        ]

    messages = get_deserialized_message_for_batches(dynamodb_client, message_table.name, message_keys)
    response_data = {
        "topic": topic_topic,
        "goal": topic_goal,
        "history": messages,
        "state": topic_state,
        "lang_id" : topic_langid,
        "lang_name" : topic_langname,
        "monaco_name": topic_monaconame,
        }
    return make_response(jsonify(response_data), 200)

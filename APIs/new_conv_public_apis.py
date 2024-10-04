from flask import Flask, redirect, url_for, request, jsonify, stream_with_context, Blueprint
from flask_dance.contrib.google import make_google_blueprint, google
from conv_handler.Conv_handler_improved_mem import TeachingAssistant_stream
from flask_login import UserMixin, LoginManager, logout_user, login_user, login_required, current_user
from auth2 import auth, max_topic_messages_WO_sub, max_topic_topics_WO_sub #, blueprint
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from flask import render_template, make_response, stream_with_context, Response
from conv_creator.Conv_Creator_basics import ConvCreator_stream
import config
from text_to_speech.TTS import TTS_blueprint
import random
import uuid 

public_blueprint = Blueprint('public', __name__)


@public_blueprint.route('/api/v1/create_conv_id_public', methods=['POST'])
def Create_conv_id_public():
    new_id = str(uuid.uuid4())
    response = {
       'id': new_id
    }
    return jsonify(response), 200

@public_blueprint.route('/api/v1/Conv_first_massage_public', methods=['POST'])
def Conv_first_massage_public():
    current_user_email = 'user@public.com'
    data = request.get_json()
    conv_id = data['id']
    response = config.user_table.get_item(Key={'email': current_user_email})
    if 'Item' not in response:
        return jsonify({"error": "User not found"}), 404
    user = response['Item']
    CC = ConvCreator_stream(
        api_keys=config.API_KEYS,
        conversation_model = config.conversation_model, 
        extraction_model = config.extraction_model, 
        temperature=0, 
        conv_id = conv_id,
        )
    return Response(CC.handle_first_message(user), mimetype='text/event-stream')


@public_blueprint.route('/api/v1/Conv_next_massage_public', methods=['POST'])
def Conv_next_massage_public():
    current_user_email = 'user@public.com'
    response = config.user_table.get_item(Key={'email': current_user_email})
    if 'Item' not in response:
        return jsonify({"error": "User not found"}), 404
    user = response['Item']
    data = request.get_json()
    user_input = data['user_input']
    conv_id = data['id']
    CC = ConvCreator_stream(
        api_keys=config.API_KEYS, 
        conversation_model = config.conversation_model, 
        extraction_model = config.extraction_model, 
        temperature=0,
        conv_id = conv_id,
        )
    return Response(CC.handle_message(user_input, user), mimetype='text/event-stream')

@public_blueprint.route('/api/v1/get_response_stream_public', methods=['POST'])
def get_response_public():
    current_user_email = 'user@public.com'
    response = config.user_table.get_item(Key={'email': current_user_email})
    if 'Item' not in response:
        return jsonify({"error": "User not found"}), 404
    user = response['Item']
    data = request.get_json()
    user_input = data['user_input']
    topic_id = data['id']
    response = config.Topics_table.get_item(
            Key={
                'userId': current_user_email,
                'topics_id': topic_id,
            }
            )
    topic = response['Item']
    
    if len(topic.get('messages',[])) >= config.maximum_chat_messages_without_login:
        response = {
            "error": "You need to sign in to continue the conversation.",
            "SigninError": True
        }
        return make_response(jsonify(response), 403)

    ta = TeachingAssistant_stream(
        api_keys=config.API_KEYS,
        conversation_model = config.conversation_model,
        extraction_model = config.extraction_model,
        temperature=0.4,
        max_tokens=5000
        )
    return Response(ta.handle_message(user_input, user['email'], topic_id), mimetype='text/event-stream')



@public_blueprint.route('/api/v1/wizard_details_public', methods=['GET'])
def wizard_details_public():
    # Fetch the item from the database
    item = config.asset_table.get_item(Key={'asset_name': 'wizardpics'}).get('Item')
    # Check if the item exists and contains 'wizardpics'
    print(item['pics'])
    if not item or 'pics' not in item or not isinstance(item['pics'], list):
        return jsonify({'error': 'Wizard pictures not found'}), 404

    # Select a random URL from the list of URLs
    random_url = random.choice(item['pics'])

    response = {
       'image': random_url,
       'name': 'Tutor Creator'
    }

    return jsonify(response), 200

@public_blueprint.route('/api/v1/buddy_details_public', methods=['GET'])
def buddy_details_public():
    # Fetch the item from the database
    item = config.asset_table.get_item(Key={'asset_name': 'buddypics'}).get('Item')

    # Check if the item exists and contains 'wizardpics'
    if not item or 'pics' not in item or not isinstance(item['pics'], list):
        return jsonify({'error': 'Tutor pictures not found'}), 404

    # Select a random URL from the list of URLs
    random_url = random.choice(item['pics'])

    response = {
       'image': random_url,
       'name': 'Tutor'
    }

    return jsonify(response), 200



@public_blueprint.route('/api/v1/Get_created_topic_public', methods=['POST'])
def get_created_topic_public():
    current_user_email = 'user@public.com'
    data = request.get_json()
    conv_id = data['id']
    conv = config.conversations_table.get_item(
        Key={
                    'conv_id':conv_id, 
                }
    )['Item']
    topic_id = conv.get('topic_id')
    last_topic = config.Topics_table.get_item(
            Key={
                    'userId': current_user_email,  # replace with your userId
                    'topics_id': topic_id  # replace with your topicId
                }
            )['Item']
    category = last_topic.get('category', "1")
    icons = config.asset_table.get_item(
            Key={
                    'asset_name': 'icon',  # replace with your userId
                })['Item']
    return jsonify({
        "Topic": last_topic['topic'], 
        "Goal": last_topic['goal'], 
        "id": topic_id, 
        "lang_id": last_topic['langid'], 
        "lang_name": last_topic["lang_name"], 
        "monaco_name": last_topic["monaco_name"], 
        'icon' : icons.get(category, icons['1'])  
        })


@public_blueprint.route('/api/v1/assign_topic_to_user', methods=['POST'])
@jwt_required()
def get_created_topic():
    current_user_email = get_jwt_identity()
    public_user_email = 'user@public.com'
    ## retrive topic
    data = request.get_json()
    topic_id = data['id']
    response = config.Topics_table.get_item(
            Key={
                'userId': public_user_email,
                'topics_id': topic_id,
            }
            )
    topic = response['Item']
    ## update topic
    topic['userId'] = current_user_email 
    config.Topics_table.put_item(Item=topic)
    config.user_table.update_item(
        Key={
            'email': current_user_email,  # replace with the actual userId
        },
        UpdateExpression="SET created_topics = list_append(created_topics, :i)",
        ExpressionAttributeValues={
            ':i': [topic_id],  # replace with the actual new topic ID
        },
        ReturnValues="UPDATED_NEW"
    )

    return jsonify({'message': 'Success'}), 200

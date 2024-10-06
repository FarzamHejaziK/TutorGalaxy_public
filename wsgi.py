from flask import Flask, redirect, url_for, request, jsonify, stream_with_context
from flask_dance.contrib.google import make_google_blueprint, google
from conv_handler.Conv_handler_improved_mem import TeachingAssistant_stream
from flask_login import UserMixin, LoginManager, logout_user, login_user, login_required, current_user
from auth2 import auth, max_topic_messages_WO_sub, max_topic_topics_WO_sub #, blueprint
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
import os
from flask import render_template, make_response, stream_with_context, Response
from dotenv import load_dotenv
import time
from conv_creator.Conv_Creator_basics import ConvCreator_stream
from config import *
from flask_cors import CORS
from datetime import timedelta
from code_excecution.code_execute import code_execution
from payment.stripe_subscription import payments_blueprint
from APIs.new_conv_public_apis import public_blueprint 
from APIs.User_Tutor_History import tutor_history_blueprint
from APIs.chat_history import chat_history_blueprint
from APIs.page_wise_chat_history import page_wise_chat_history_blueprint
from text_to_speech.TTS import TTS_blueprint
import random
import sys
from boto3.dynamodb.types import TypeDeserializer





# Load environment variables from .env file
load_dotenv()

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

max_topic_messages_WO_sub = 5000
max_topic_topics_WO_sub = 200

app = Flask(__name__)
CORS(app, origins=['http://localhost:3000','https://vocoverse.com','https://tutor-galaxy.com'])
app.secret_key = os.getenv("SECRET_KEY")  # replace with your secret key
app.config['JWT_SECRET_KEY'] = os.getenv("JWT_SECRET_KEY")  # Change this!
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=30)  # Example: 30 minutes
app.config['THREADING'] = True
jwt = JWTManager(app)

app.register_blueprint(auth)
login_manager = LoginManager()
login_manager.init_app(app)


## register APIs
app.register_blueprint(payments_blueprint, url_prefix='/payments')
app.register_blueprint(TTS_blueprint)
app.register_blueprint(public_blueprint)
app.register_blueprint(tutor_history_blueprint)
app.register_blueprint(chat_history_blueprint)
app.register_blueprint(page_wise_chat_history_blueprint)

@login_manager.user_loader
def load_user(user_id):
    response = user_table.get_item(Key={'userId': user_id})
    if 'Item' in response:
        return User(response['Item'])
    else:
        return None



API_KEYS = os.getenv("API_KEYS").split(',')



@app.route('/api/v1/get_response_stream', methods=['POST'])
@jwt_required()
def get_response():
    current_user_email = get_jwt_identity()
    response = user_table.get_item(Key={'email': current_user_email})
    if 'Item' not in response:
        return jsonify({"error": "User not found"}), 404
    user = response['Item']
    subscribed = user.get('subscribed', {}).get('state', False)
    data = request.get_json()
    user_input = data['user_input']
    topic_id = data['id']
    response = Topics_table.get_item(
            Key={
                'userId': current_user_email,
                'topics_id': topic_id,
            }
            )
    topic = response['Item']
    if not subscribed:   
        if len(topic.get('messages',[])) >= max_topic_messages_WO_sub:
            response = {
                "error": "You need a subscription to continue this conversation.",
                "subscriptionError": not subscribed
            }
            return make_response(jsonify(response), 403)

    if topic.get('category') == '3': 
        temperature = 0.8
    else:
        temperature = 0.4

    ta = TeachingAssistant_stream(api_keys=API_KEYS, conversation_model = conversation_model, extraction_model = extraction_model, temperature=temperature, max_tokens=5000)
    return Response(ta.handle_message(user_input, user['email'], topic_id), mimetype='text/event-stream')


@app.route('/api/v1/wizard_details', methods=['GET'])
@jwt_required()
def wizard_details():
    # Fetch the item from the database
    item = asset_table.get_item(Key={'asset_name': 'wizardpics'}).get('Item')
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

@app.route('/api/v1/buddy_details', methods=['GET'])
@jwt_required()
def buddy_details():
    # Fetch the item from the database
    item = asset_table.get_item(Key={'asset_name': 'buddypics'}).get('Item')

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
    

    


@app.route('/api/v1/Conv_first_massage', methods=['POST'])
@jwt_required()
def Conv_first_massage():
    current_user_email = get_jwt_identity()
    response = user_table.get_item(Key={'email': current_user_email})
    if 'Item' not in response:
        return jsonify({"error": "User not found"}), 404
    user = response['Item']
    subscribed = user.get('subscribed', {}).get('state', False)
    if not subscribed:
        if len(user['created_topics']) >= max_topic_topics_WO_sub:
            response = {
                "error": "You need a subscription to create new topics.",
                "subscriptionError": not subscribed
            }
            return make_response(jsonify(response), 403)
    CC = ConvCreator_stream(api_keys=API_KEYS, conversation_model = conversation_model, extraction_model = extraction_model, temperature=0)
    return Response(CC.handle_first_message(user), mimetype='text/event-stream')



@app.route('/api/v1/Conv_next_massage', methods=['POST'])
@jwt_required()
def Conv_next_massage():
    current_user_email = get_jwt_identity()
    response = user_table.get_item(Key={'email': current_user_email})
    if 'Item' not in response:
        return jsonify({"error": "User not found"}), 404
    user = response['Item']
    subscribed = user.get('subscribed', {}).get('state', False)
    if not subscribed:
        if len(user['created_topics']) >= max_topic_topics_WO_sub:
            response = {
                "error": "You need a subscription to create new topics.",
                "subscriptionError": not subscribed  # This will always be True in this block, but using `not subscribed` makes it clear.
            }
            return make_response(jsonify(response), 403)
    data = request.get_json()
    user_input = data['user_input']
    CC = ConvCreator_stream(api_keys=API_KEYS, conversation_model = conversation_model, extraction_model = extraction_model, temperature=0)
    return Response(CC.handle_message(user_input, user), mimetype='text/event-stream')

@app.route('/api/v1/Get_created_topic', methods=['POST'])
@jwt_required()
def get_created_topic():
    current_user_email = get_jwt_identity()
    response = user_table.get_item(Key={'email': current_user_email})
    if 'Item' not in response:
        return jsonify({"error": "User not found"}), 404
    user = response['Item']
    if not user['created_topics']:
        return jsonify({"error": "No topics found for the user"}), 404
    topic_id = user['created_topics'][-1]
    last_topic = Topics_table.get_item(
            Key={
                    'userId': user['email'],  # replace with your userId
                    'topics_id': topic_id  # replace with your topicId
                }
            )['Item']
    category = last_topic.get('category', "1")
    icons = asset_table.get_item(
            Key={
                    'asset_name': 'icon',  # replace with your userId
                })['Item']
    return jsonify({"Topic": last_topic['topic'], "Goal": last_topic['goal'], "id": topic_id, "lang_id": last_topic['langid'], "lang_name": last_topic["lang_name"], "monaco_name": last_topic["monaco_name"], 'icon' : icons.get(category, icons['1'])  })




@app.route('/api/v1/user_details', methods=['GET'])
@jwt_required()
def get_user_profile_v2():
    try:
        current_user_email = get_jwt_identity()
        response = user_table.get_item(Key={'email': current_user_email})

        # Check if user exists
        if 'Item' not in response:
            return jsonify({"error": "User not found"}), 404

        user = response['Item']

        # Check topic creation permission
        subscribed = user.get('subscribed', {}).get('state', False)
        user_create_topic_permission = True
        if not subscribed:
            if len(user.get('created_topics', [])) >= max_topic_topics_WO_sub:
                user_create_topic_permission = False

        if 'screen_mode' not in user:
            user['screen_mode'] = 1

            user_table.update_item(
                Key={'email': current_user_email},
                UpdateExpression="SET screen_mode = :mode_value",
                ExpressionAttributeValues={
                    ':mode_value': 1
                }
            )

    

        # Prepare final response
        result = {
            'given_name': user.get('given_name'),
            'family_name': user.get('family_name'),
            'photo': user.get('photo'),
            'user_create_topic_permission': user_create_topic_permission,
            'isSubscribed': subscribed,
            'screen_mode': user.get('screen_mode')
        }

        return jsonify(result), 200

    except Exception as e:
        print(e)
        return jsonify({"error": "An unexpected error occurred."}), 500


@app.route('/api/v1/change_mode', methods=['POST'])
@jwt_required()
def change_user_mode():
    try:
        current_user_email = get_jwt_identity()
        data = request.get_json()

        # Update the user item in the DynamoDB table
        user_table.update_item(
            Key={'email': current_user_email},
            UpdateExpression="SET screen_mode = :mode_value",
            ExpressionAttributeValues={
                ':mode_value': data.get('screen_mode', 1)
            }
        )

        return jsonify({"message": "Mode updated successfully"}), 200

    except Exception as e:
        print(e)
        return jsonify({"error": "An unexpected error occurred."}), 500

'''
@app.route('/api/v1/chat_history', methods=['POST'])
@jwt_required()
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
    messages = []
    for message_id in topic['messages']:
        response = message_table.get_item(
                Key={
                    'topics_id': topic_id,
                    'message_id': message_id,
                }
            )
        message_item = response['Item']
        messages.append(message_item['message'])
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
'''
    
@app.route('/api/v1/code_excecution', methods=['POST'])
@jwt_required()
def code_excecution():
    current_user_email = get_jwt_identity()
    response = user_table.get_item(Key={'email': current_user_email})
    if 'Item' not in response:
        return jsonify({"error": "User not found"}), 404

    user = response['Item']
    subscribed = user.get('subscribed', {}).get('state', False)
    '''if not subscribed:
        response = {
            "error": "You need a subscription to execute code.",
            "isSubscribed": subscribed
        }
        return make_response(jsonify(response), 403)'''
    data = request.get_json()
    topic_id = data.get('id')  
    code = data.get('code')
    stdin = data.get('stdin',"")
    
    if not code:
        return jsonify({"error": "code not provided"}), 400
    langid = data.get('lang_id')
    if not langid:
        return jsonify({"error": "lang_id not provided"}), 400
    try:
        langid = int(langid)
    except ValueError:
        return jsonify({"error": "lang_id should be an integer or a string representation of an integer"}), 400

    Topics_table.update_item(
            Key={
                'userId': current_user_email,
                'topics_id': topic_id,
            },
            UpdateExpression="SET code_editor_used = :codeEditorValue",
            ExpressionAttributeValues={
                ':codeEditorValue': 1,
            },
            ReturnValues="UPDATED_NEW"
        )
    result, status_code = code_execution(langid, code, stdin)
    return jsonify(result), status_code


@app.route('/api/v1/text_editor', methods=['POST'])
@jwt_required()
def text_editor():
    current_user_email = get_jwt_identity()
    response = user_table.get_item(Key={'email': current_user_email})
    if 'Item' not in response:
        return jsonify({"error": "User not found"}), 404
    data = request.get_json()
    topic_id = data.get('id')
    try:
        Topics_table.update_item(
            Key={
                'userId': current_user_email,
                'topics_id': topic_id,
            },
            UpdateExpression="SET text_editor_used = :textEditorValue",
            ExpressionAttributeValues={
                ':textEditorValue': 1,
            },
            ReturnValues="UPDATED_NEW"
        )
        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


    



@app.route('/')
def home():
    return "Home Page"

@app.route('/health')
def health_check():
    return "OK", 200


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)

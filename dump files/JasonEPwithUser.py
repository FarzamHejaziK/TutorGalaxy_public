from flask import Flask, redirect, url_for, request, jsonify, stream_with_context
from flask_dance.contrib.google import make_google_blueprint, google
from Conv_handler_improved_mem import TeachingAssistant_stream
from flask_login import UserMixin, LoginManager, logout_user, login_user, login_required, current_user
from auth2 import auth, max_topic_messages_WO_sub, max_topic_topics_WO_sub #, blueprint
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
import os
from flask import render_template, make_response, stream_with_context, Response
from dotenv import load_dotenv
import time
#from conv_creator import ConvCreator_stream
from NewConvCreator import ConvCreator_stream
from config import user_table, Topics_table, message_table  
from flask_cors import CORS
from datetime import timedelta
from code_excecution.code_execute import code_execution
from payment.stripe_subscription import payments_blueprint
from text_to_speech.TTS import TTS_blueprint





# Load environment variables from .env file
load_dotenv()


os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'


app = Flask(__name__)
CORS(app, origins=['http://localhost:3000','https://vocoverse.com'])
app.secret_key = os.getenv("SECRET_KEY")  # replace with your secret key
app.config['JWT_SECRET_KEY'] = os.getenv("JWT_SECRET_KEY")  # Change this!
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=30)  # Example: 30 minutes
app.config['THREADING'] = True
jwt = JWTManager(app)



app.register_blueprint(auth)
login_manager = LoginManager()
login_manager.init_app(app)

app.register_blueprint(payments_blueprint, url_prefix='/payments')
app.register_blueprint(TTS_blueprint)


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
    if not subscribed:
        response = Topics_table.get_item(
            Key={
                'userId': current_user_email,
                'topics_id': topic_id,
            }
            )
        topic = response['Item']
        if len(topic['messages']) >= max_topic_messages_WO_sub:
            response = {
                "error": "You need a subscription to continue this conversation.",
                "subscriptionError": not subscribed
            }
            return make_response(jsonify(response), 403)


    ta = TeachingAssistant_stream(api_keys=API_KEYS, model_engine="gpt-4", temperature=0.7, max_tokens=5000)
    return Response(ta.handle_message(user_input, user['email'], topic_id), mimetype='text/event-stream')


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
    CC = ConvCreator_stream(api_keys=API_KEYS, model_engine="gpt-4", temperature=0)
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
    CC = ConvCreator_stream(api_keys=API_KEYS, model_engine="gpt-4", temperature=0)
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
    return jsonify({"Topic": last_topic['topic'], "Goal": last_topic['goal'], "id": topic_id, "lang_id": last_topic['langid'], "lang_name": last_topic["lang_name"], "monaco_name": last_topic["monaco_name"] })


@app.route('/api/v1/user_profile', methods=['GET'])
@jwt_required()
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
        for topic_id in reversed(user['created_topics']):
            topic = Topics_table.get_item(
            Key={
                    'userId': current_user_email,  # replace with your userId
                    'topics_id': topic_id  # replace with your topicId
                }
            )['Item']
            langid = topic.get('langid', "-1")
            langname = topic.get('lang_name', "-1")
            monaconame = topic.get('monaco_name', "-1")
            

            current_topic= {
                'topic': topic['topic'],
                'goal': topic['goal'],
                'id': topic['topics_id'],
                'state': topic['state'],
                'lang_id': str(langid),
                'lang_name' : str(langname),
                'monaco_name': monaconame, 
                'create_topic_permission': user_create_topic_permission,
            }
            topics_goals.append(current_topic)
        return make_response(jsonify(topics_goals), 200)
    else:
        return jsonify({"error": "No topics found for the user"}), 404


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

    

        # Prepare final response
        result = {
            'given_name': user.get('given_name'),
            'family_name': user.get('family_name'),
            'photo': user.get('photo'),
            'user_create_topic_permission': user_create_topic_permission,
            'isSubscribed': subscribed
        }

        return jsonify(result), 200

    except Exception as e:
        print(e)
        return jsonify({"error": "An unexpected error occurred."}), 500


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

import os
from flask import Flask, jsonify, request, Blueprint, Response
from google.cloud import texttospeech
from dotenv import load_dotenv
from config import user_table, Topics_table, message_table  
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
import emoji
import re



# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

TTS_blueprint = Blueprint('TTS', __name__)

speaking_rate = 1

def remove_prefix(text):
    if text.startswith("system:"):
        return text[len("system:"):].strip()
    elif text.startswith("user:"):
        return text[len("user:"):].strip()
    else:
        return text

def clean_text(text):
    ## Remove Bolds
    clean_string = text.replace("**", "")
    ## Remove Emojies
    clean_string = emoji.replace_emoji(clean_string, '')
    ## Replace Code Snippets
    pattern = r"```(.*?)\n(.*?)```"
    replacement = lambda m: f'\n code snippet in {m.group(1)}.\n'
    clean_string = re.sub(pattern, replacement, clean_string, flags=re.DOTALL)
    ## Remove backqoutes
    pattern = r'``?(.*?)``?'
    replacement = r'\1'
    clean_string = re.sub(pattern, replacement, clean_string)
    return clean_string 


@TTS_blueprint.route('/v1/TTS', methods=['POST'])
def synthesize_speech():
    text = clean_text(remove_prefix(request.json.get('text', ''))) 
    current_user_email = get_jwt_identity()
    topic_id = request.json.get('id', None)
    if len(text) == 0:
        topic = Topics_table.get_item(
            Key={
                    'userId': current_user_email,  # replace with your userId
                    'topics_id': topic_id  # replace with your topicId
                }
            )['Item']
        for message_id in reversed(topic['messages']):
            response = message_table.get_item(
                Key={
                    'topics_id': topic_id,
                    'message_id': message_id,
                }
            )
            message = response['Item']['message']
            if not message.startswith("user:"):
                text = clean_text(remove_prefix(message)) # This is the first message from the end that doesn't start with "user:"
                break

    client = texttospeech.TextToSpeechClient()
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US", 
        name="en-US-Neural2-C",  # Specify the desired voice name here
        ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
    )
    audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.LINEAR16,speaking_rate=speaking_rate)

    response = client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)

    # Return audio content directly
    return Response(response.audio_content, content_type='audio/wav')







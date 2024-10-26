import boto3
from dotenv import load_dotenv
import os

dynamodb = boto3.resource('dynamodb', region_name='us-west-1')  # replace 'us-west-2' with your preferred region
dynamodb_client = boto3.client('dynamodb', region_name='us-west-1')

user_table = dynamodb.Table('User')
conversations_table = dynamodb.Table('Conversations')
Topics_table = dynamodb.Table('Topics')
message_table = dynamodb.Table('messages')
asset_table = dynamodb.Table('Assets')

# Params 
model_engine = 'gpt-4o'
conversation_model = 'gpt-4o'
extraction_model = 'gpt-4o' 
maximum_chat_messages_without_login = 10
max_topic_messages_WO_sub = 50
max_topic_topics_WO_sub = 8
message_per_page = 10

# API_KEYS
load_dotenv()
API_KEYS = os.getenv("OPENAI_API_KEYS").split(',')
MODE = "test" 

import boto3

dynamodb = boto3.resource('dynamodb', region_name='us-west-1')  # replace 'us-west-2' with your preferred region
user_table = dynamodb.Table('User')
conversations_table = dynamodb.Table('Conversations')
Topics_table = dynamodb.Table('Topics')
message_table = dynamodb.Table('messages')

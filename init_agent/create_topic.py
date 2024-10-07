import re
import uuid
from config import Topics_table, user_table, conversations_table
from botocore.exceptions import ClientError
from .summarizers import summarizer 
from .chat_prompt_creator.Fixed_chat_prompt import Fixed_prompt
from .chat_prompt_creator.Planning_chat_prompt import Planning    
from .chat_prompt_creator.Excecution_chat_prompt import Excecution
from .chat_prompt_creator.Post_Excecution_chat_prompt import Post_Excecution
from datetime import datetime
import pytz

def serialized_text(text):
    return ' '.join(text.split())

def create_topic_method(self, post_sequence_string):
    keys = ['chatstarter', 'chat']
    parsed_values = {}
    #print("input", post_sequence_string)
    for key in keys:
        # Construct the regex pattern to match 'Key'="Value",
        pattern = r'"' + key + r'"\s*:\s*"([^"]*)'
        match = re.search(pattern, post_sequence_string)
        if match:
            parsed_values[key] = match.group(1).strip()
    
    topic = self.topic_details.get("topic")
    goal = self.topic_details.get("goal")
    chatstarter = parsed_values.get("chatstarter")
    who_you_are = parsed_values.get("chat")
    langid = self.topic_details.get("langid")
    langname = self.topic_details.get("lang_name")
    monaconame = self.topic_details.get("monaco_name")
    #learning = self.topic_details.get("learning")
    #creativity = self.topic_details.get("creativity")
    #GQA = self.topic_details.get("GQA")
    nickname = self.topic_details.get("nickname")
    #secrets_revealed = self.topic_details.get("secrets_revealed")
    #user_pref = self.topic_details.get("user_pref")
    category = self.topic_details.get("category")
    #learning_persona = self.topic_details.get("learning_persona")
    #creative_persona = self.topic_details.get("creative_persona")
    #learning_style = self.topic_details.get("learning_style")
    persona_pref = self.topic_details.get("persona_pref")
    tutor_bahaviour = self.topic_details.get("tutor_bahaviour", 1)

    
    
    ## Prompts
    
    summarizer_prompt = summarizer.get(category,self.default_summary)
    
    Planning_prompt = Planning.get(category,'') 
    
    Planning_prompt = serialized_text(who_you_are + Planning_prompt) 

    Excecution_prompt = Excecution.get(category,'')

    Excecution_prompt = serialized_text(who_you_are + Excecution_prompt) 

    Post_Excecution_prompt = Post_Excecution.get(category,'')

    Post_Excecution_prompt = serialized_text(who_you_are + Post_Excecution_prompt) 
    

    new_topic_id = str(uuid.uuid4()) 

    #time 
    pst = pytz.timezone('America/Los_Angeles')
    current_time_pst = datetime.now(pst).strftime('%Y-%m-%d %H:%M:%S')

    new_topic = {
        'userId': self.user_email,
        'topics_id': new_topic_id,
        'goal' : goal,
        'topic' : topic,
        'chatstarter' : chatstarter,
        'Planning_prompt': Planning_prompt,
        'Excecution_prompt': Excecution_prompt,
        'Post_Excecution_prompt': Post_Excecution_prompt,
        'langid' : langid,
        'lang_name' : langname,
        'monaco_name': monaconame,
        'category': category, 
        'persona_pref': persona_pref,
        'text_editor_used' : 0,
        'code_editor_used' : 0,
        'summarizer_prompt': summarizer_prompt,
        'state' : 0,
        'summary': "",
        'messages':[],
        'messages_queue':[],
        'Planning_done': False,
        'Excecution_done': False,
        'who_you_are': who_you_are,
        "tutor_bahaviour": tutor_bahaviour,
        'timestamp': current_time_pst,
    }
    response =  Topics_table.put_item(Item=new_topic)

    # Check if the operation was successful
    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
        print("The new topic was successfully inserted.")
        # You can continue to the next line of code here
    else:
        print("Failed to insert the new topic.")

    user_table.update_item(
        Key={
            'email': self.user_email,  # replace with the actual userId
        },
        UpdateExpression="SET created_topics = list_append(if_not_exists(created_topics, :empty_list), :i)",
        ExpressionAttributeValues={
            ':i': [new_topic_id],  # replace with the actual new topic ID
            ':empty_list': []  # Define the empty list here
        },
        ReturnValues="UPDATED_NEW"
    )


    if nickname != self.user.get('nickname') and nickname != None or '-1' :
        user_table.update_item(
            Key={'email': self.user_email},
            UpdateExpression='SET nickname = :val1',
            ExpressionAttributeValues={
                ':val1': nickname
            }
        )
    
    if self.conv_id:
        conversations_table.update_item(
            Key={'conv_id': self.conv_id},
            UpdateExpression="SET topic_id = :id",
            ExpressionAttributeValues={
                ':id': new_topic_id
            }
        )



    '''
    if secrets_revealed != 'none':
        try:
            user_table.update_item(
                Key={'email': self.user_email},
                UpdateExpression='SET secrets_revealed = list_append(secrets_revealed, :val1)',
                ConditionExpression='attribute_exists(secrets_revealed)',
                ExpressionAttributeValues={
                    ':val1': [secrets_revealed],  # Assuming secrets_revealed is a single value.
                }
            )
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                # The attribute doesn't exist, so set the attribute with the new value.
                user_table.update_item(
                    Key={'email': self.user_email},
                    UpdateExpression='SET secrets_revealed = :val1',
                    ExpressionAttributeValues={
                        ':val1': [secrets_revealed],  # Assuming secrets_revealed is a single value.
                    }
                )'''

    return
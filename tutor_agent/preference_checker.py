from config import Topics_table
import re
import time 
import random
import openai

prompt= """ These are the last 4 messages between the user and the system : [begin] {} [end].
You are given these messages to understand the context of the conversation. This is the last message of the user: {}. 
If the user expressed any preferences about the conversation in the last message extract that. 
Note that: user may answered a question, may ask a question, may continue conversation.
these are not prefernces. If user want the conversation to be in some form or sytems answers have some specfic attributes and simialr stuff, these are user prefernces.

Then give me the extracted info in this format and nothing else:
    "user_prefer":"<your extracted preference>",

if the user did not express any preference in the last message just output: null
      """

def concatenate_with_spaces(arr):
    result = ""
    for string in arr:
        result += string + " "
    result = result.rstrip()  # Remove trailing space
    return result


def preference_check_method(self,user_input):

    last_4_messages = self.messages_queue[:4]
    prompt= f"""
This is the last message of the user: {user_input} 
If the user expressed any preferences or demand extract that. what you extract should be very short at most 5 words.

Then give me the extracted info in this format and nothing else:
    "user_prefer":"<your extracted preferenceor demand>",

if the user did not express any preference in the last message just output: null
      """
    max_retries = len(self.api_keys)+2
    retries = 0
    while retries <= max_retries:
        try:
            # Randomly select an API key for each call
            openai.api_key = self.api_keys[retries % len(self.api_keys)]
            parsed_response = openai.ChatCompletion.create(
                model = self.extraction_model,
                messages=[
                    {"role": "system", "content":prompt},
                ],
                temperature = 0,
                max_tokens = self.chat_max_tokens
            )
            content = parsed_response["choices"][0]["message"]["content"]
            self.get_prefer(content)
            return
        except Exception as e:
            print(f"Error in chat method: {e}")
            retries += 1
            if retries <= max_retries:
                print("Retrying with a new API key...")
                time.sleep(1)
            else:
                return "Sorry, there was an issue connecting to the API. Please try again later."

def get_prefer_method(self,content):
    keys = ['user_prefer']
    parsed_values = {}
    #print("input", post_sequence_string)
    for key in keys:
        # Construct the regex pattern to match 'Key'="Value",
        pattern = r'"' + key + r'"\s*:\s*"([^"]*)'
        match = re.search(pattern, content)
        if match:
            parsed_values[key] = match.group(1).strip()
    
    user_prefer = parsed_values.get("user_prefer", None)
    print('extracted prefere:' , user_prefer)
    if user_prefer: 
        Topics_table.update_item(
            Key={
                'userId': self.user_email,
                'topics_id': self.topic_id,
            },
            UpdateExpression="SET user_prefer = list_append(if_not_exists(user_prefer, :empty_list), :new_value)",
            ExpressionAttributeValues={
                ':empty_list': [],
                ':new_value': [user_prefer],
            },
            ReturnValues="UPDATED_NEW"
        )

    


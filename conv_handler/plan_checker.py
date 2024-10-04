from mytiktoken import count_tokens
import re
import time 
import random
import openai
from config import Topics_table


def concatenate_with_spaces(arr):
    result = ""
    for string in arr:
        result += string + " "
    result = result.rstrip()  # Remove trailing space
    return result

def plan_checker_method(self,user_input):
    print('checking for plan')
    covered_topics = concatenate_with_spaces(self.covered_arr_to_set(self.topic.get('topics_covered',['0'])))
    prompt= f"""  
        This is conversation between the user and the system: [begin] {concatenate_with_spaces(self.messages_queue) + 'user: ' + user_input} [end].
        Please check if 'the system already planned for the learning path' AND 'the user approved the system plan'.
        the plan is a detailed description of all the sessions (or topics) like this: (1-session 1: 1-1-topic1 1-2- topic-2 ..., 2- sessions 2: 1-1-topic1 1-2- topic-2 ...) (the system may use another word than session).
        
        Your check output is True or False.
        and then output in the following format: 
        "check":"True or False",
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
            return self.plan_check(content) == 'True'
        except Exception as e:
            print(f"Error in chat method: {e}")
            retries += 1
            if retries <= max_retries:
                print("Retrying with a new API key...")
                time.sleep(1)
            else:
                return "Sorry, there was an issue connecting to the API. Please try again later."

def plan_check_method(self,content):
    keys = ['check']
    parsed_values = {}
    #print("input", post_sequence_string)
    for key in keys:
        # Construct the regex pattern to match 'Key'="Value",
        pattern = r'"' + key + r'"\s*:\s*"([^"]*)'
        match = re.search(pattern, content)
        if match:
            parsed_values[key] = match.group(1).strip()
    print(f'Plan check results: {parsed_values.get("check")}')
    return parsed_values.get("check")

def add_plan_to_topic_method(self):
    Topics_table.update_item(
        Key={
            'userId': self.user_email,
            'topics_id': self.topic_id,
        },
        UpdateExpression="SET tempplan = :i",
        ExpressionAttributeValues={
            ':i': True,
        },
        ReturnValues="UPDATED_NEW"
    )
from config import Topics_table, message_table, user_table
from mytiktoken import count_tokens
import re
import time 
import random
import openai

def concatenate_with_spaces(arr):
    result = ""
    for string in arr:
        result += string + " "
    result = result.rstrip()  # Remove trailing space
    return result


def find_last_covered_method(self,content):

    covered_topics = concatenate_with_spaces(self.covered_arr_to_set(self.topic.get('topics_covered',['0'])))
    unique_values = set()
    for item in covered_topics:
        unique_values.update(item.split(','))
    covered_topics = sorted(unique_values)

    prompt = f""" Plan Tracking Prompt: 

    - Outline of Plan: [begin] {self.plan} [end].
    - Recently Covered Topics: [last_covered]: {covered_topics}.
    - Last 10 Messages: [begin] {concatenate_with_spaces(self.messages_queue[-10:])} [end].

    Task: Identify any plan topics covered in the last 10 messages not listed in [last_covered].

    Criteria for Covered Topics:
    1. Topic must be explicitly started by the system, including its number and name.
    2. Topic must be comprehensively covered and concluded.
    3. Topics should be covered sequentially. If a topic like 2.1 is discussed, but an intervening topic (like 1.5) has not been covered, 2.1 is not considered fully covered.
    4. Re-check for explicit mention and comprehensive coverage for precision.

    Output: 
    - If new topics are covered, format as: "covered":"<extracted topic numbers>".
    - If no new topics are covered, return: null.
    """
    #print("covered Prompt", prompt)
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
            self.get_covered(content)
            return
        except Exception as e:
            print(f"Error in chat method: {e}")
            retries += 1
            if retries <= max_retries:
                print("Retrying with a new API key...")
                time.sleep(1)
            else:
                return "Sorry, there was an issue connecting to the API. Please try again later."


def get_covered_method(self,content):
    keys = ['covered']
    parsed_values = {}
    #print("input", post_sequence_string)
    for key in keys:
        # Construct the regex pattern to match 'Key'="Value",
        pattern = r'"' + key + r'"\s*:\s*"([^"]*)'
        match = re.search(pattern, content)
        if match:
            parsed_values[key] = match.group(1).strip()
    
    topics_covered = parsed_values.get("covered")
    print("Covered now",topics_covered)
    if topics_covered: 
        Topics_table.update_item(
            Key={
                'userId': self.user_email,
                'topics_id': self.topic_id,
            },
            UpdateExpression="SET topics_covered = list_append(if_not_exists(topics_covered, :empty_list), :new_value)",
            ExpressionAttributeValues={
                ':empty_list': [],
                ':new_value': [topics_covered],
            },
            ReturnValues="UPDATED_NEW"
        )

def covered_arr_to_set_method(self,covered):
    unique_topics = set()
    for entry in covered:
        # Extract the string of topics
        # Step 3: Split the string by comma to get individual topics
        topics = entry.split(',')
        # Step 4: Add each topic to the set
        unique_topics.update(topics)
    return sorted(list(unique_topics)) 

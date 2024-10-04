import openai
import time
import random
import asyncio
from config import Topics_table, message_table, user_table
import tiktoken
import os
from dotenv import load_dotenv
import time
from mytiktoken import count_tokens
from math import floor






def concatenate_with_spaces(arr):
    result = ""
    for string in arr:
        result += string + " "
    result = result.rstrip()  # Remove trailing space
    return result

class TeachingAssistant_stream:
    def __init__(self, api_keys, model_engine="gpt-4", temperature=0.7, max_tokens=5000):
        self.api_keys = api_keys
        self.model_engine = model_engine
        self.summerizer_model_engine = "gpt-4"
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.state = 0
        self.user_messages = []
        self.system_messages = []
        self.summary = None 
        self.messages_queue = []
        self.mq_len = 15
        self.discussion = None
        self.conversation_history = []
        self.chat_start_prompt = None
        self.chat_continue_prompt = None
        self.gpt_max_tokens = 8000
        self.chat_starter_max_tokens = 1000
        self.chat_max_tokens = 1000
        self.guard_tokens = 500
        self.max_summarizer_words = 2000
        self.max_token_allowed = self.gpt_max_tokens - self.chat_max_tokens - self.guard_tokens
        self.default_summary = """Summarize the conversation between 'system' and 'user'. This is the conversation: {}. 
The order of the of the conversation should remain intact. 
In your summary it should be very clear what 'system' said and what 'user' said in order. 
keep the whole summary less than {} words. 
If the text cotain the name of the 'system' or the 'user', remember to bring it in the summary intact. 
Your summay should maintain the course of conversation. Specially when the conversation took a turn.
if the system put out a plan for the conversation, bring the plan with all the details in the summary, I mean copy and paste level of details, everything, intact. The plan may get revised throgh the conversation
put the latest version with all the details in your summary.
User preferences is very important, if user express any prefernce bring put it in your summary. """ 




    
    def chatstarter(self, prompt):
            max_retries = 2
            retries = 0

            while retries <= max_retries:
                try:
                    openai.api_key = random.choice(self.api_keys)
                    
                    parsed_response = openai.ChatCompletion.create(
                        model = self.model_engine,
                        messages=[
                            {"role": "system", "content": f"{self.chat_start_prompt}"},
                            {"role": "user", "content": f"{prompt}"},
                        ],
                        temperature = self.temperature,
                        max_tokens = self.chat_starter_max_tokens,
                        stream = True
                    )
                    for line in parsed_response:
                        if 'content' in line['choices'][0]['delta']:
                            yield line['choices'][0]['delta']['content']
                    return
                except Exception as e:
                    print(f"Error in chat method: {e}")
                    retries += 1
                    if retries <= max_retries:
                        print("Retrying with a new API key...")
                        time.sleep(1)
                    else:
                        return "Sorry, there was an issue connecting to the API. Please try again later."
    
    
    def chat(self, prompt):
            max_retries = 2
            retries = 0
            while retries <= max_retries:
                try:
                    
                    openai.api_key = self.api_keys[retries % len(self.api_keys)]
                    parsed_response = openai.ChatCompletion.create(
                        model = self.model_engine,
                        messages=[
                            {"role": "system", "content": f"This is the record of the conversation that you have had with the user so far:[begin of the record of the conversation]{self.discussion}[end of the record of the conversation]. You are the system. So you continue disscusion as the system. You are the system so should never answer like this 'user = ...' . {self.chat_continue_prompt}"},
                            {"role": "user", "content": f"{prompt}"},
                        ],
                        temperature=self.temperature,
                        max_tokens=self.chat_max_tokens,
                        stream = True
                    )
                    for line in parsed_response:
                        if 'content' in line['choices'][0]['delta']:
                            yield line['choices'][0]['delta']['content']
                    return
                except Exception as e:
                    print(f"Error in chat method: {e}")
                    retries += 1
                    if retries <= max_retries:
                        print("Retrying with a new API key...")
                        time.sleep(1)
                    else:
                        return "Sorry, there was an issue connecting to the API. Please try again later."
                    
    def summarizer(self, prompt):
            max_retries = 3
            retries = 0
            prompt_tokens = count_tokens(prompt)
            prompt_words = floor(prompt_tokens*0.75)
            summary_words = max(floor(prompt_words/4), self.max_summarizer_words)
            while retries <= max_retries:
                try:
                    # Randomly select an API key for each call
                    openai.api_key = self.api_keys[retries % len(self.api_keys)]
                    parsed_response = openai.ChatCompletion.create(
                        model = self.summerizer_model_engine,
                        messages=[
                            {"role": "system", "content":self.summarizer_prompt.format(prompt, summary_words)},
                        ],
                        temperature = 0,
                        max_tokens = floor(summary_words/0.6)
                    )
                    content = parsed_response["choices"][0]["message"]["content"]
                    return content
                except Exception as e:
                    print(f"Error in chat method: {e}")
                    retries += 1
                    if retries <= max_retries:
                        print("Retrying with a new API key...")
                        time.sleep(1)
                    else:
                        return "Sorry, there was an issue connecting to the API. Please try again later."


    def handle_message(self, user_input: str, user_email, topic_id):
        self.user_email, self.topic_id = user_email, topic_id
        self.get_user_and_topic()
        for chunk in self.process_message(user_input):
            yield chunk

    def get_user_and_topic(self):
        self.topic = Topics_table.get_item(
            Key={
                    'userId': self.user_email,  # replace with your userId
                    'topics_id': self.topic_id  # replace with your topicId
                }
            )['Item']
        if not self.topic:
            return "Topic not found" 
        
        self.chat_start_prompt = self.topic['chatstarter']
        self.chat_continue_prompt = self.topic['chat']
        self.chat_continue_prompt_token_number = count_tokens(self.chat_continue_prompt)
        self.state =  self.topic['state']
        self.summary = self.topic['summary']
        self.messages_queue_ids = self.topic['messages_queue']
        self.summarizer_prompt = self.topic.get('summarizer_prompt',self.default_summary)
        self.create_messages_queue()
        return 
    
    def create_messages_queue(self):
        messages = []
        for message_id in self.messages_queue_ids:
            response = message_table.get_item(
                Key={
                    'topics_id': self.topic_id,
                    'message_id': message_id,
                }
            )
            message_item = response['Item']
            messages.append(message_item['message'])
        self.messages_queue = messages

    def process_message(self, user_input):
        if self.state == 0:
            prompt = f""
        
            # Consume the response from the chatstarter method
            full_response = []
            for chunk in self.chatstarter(prompt):
                yield chunk
                full_response.append(chunk)

            
            # Set self.system_content and execute the rest of the code once the full response has been received
            self.system_content = f"system: {''.join(full_response)}"

            self.state = 1
            self.create_message_in_db_and_update_state(self.system_content)
            self.messages_queue.append(self.system_content)

        elif self.state == 1:
            self.discussion = f"summary so far:{self.summary}, {concatenate_with_spaces(self.messages_queue)}"
            prompt = f"user: {user_input}"
            self.state = 1  
            self.create_message_in_db_and_update_state(prompt)
            self.messages_queue.append(prompt)
            # Consume the response from the chat method
            full_response = []
            for chunk in self.chat(prompt):
                yield chunk
                full_response.append(chunk)

            # Set self.system_content and execute the rest of the code once the full response has been received
            self.system_content = f"{''.join(full_response)}"
            self.create_message_in_db_and_update_state(self.system_content)
            self.messages_queue.append(self.system_content)
            prompt = f"summary so far:{self.summary}, {concatenate_with_spaces(self.messages_queue)}"
            print('token counts:',count_tokens(prompt) + self.chat_continue_prompt_token_number)
            try:
                if count_tokens(prompt) + self.chat_continue_prompt_token_number >= self.max_token_allowed:
                    self.len_purge_queue = floor(len(self.messages_queue)/2)
                    self.purge_queue = self.messages_queue[:self.len_purge_queue]
                    self.messages_queue = self.messages_queue[self.len_purge_queue:]
                    prompt = f"summary so far:{self.summary}, {concatenate_with_spaces(self.purge_queue)}"
                    yield "[REST]"
                    self.summary = self.summarizer(prompt)
                    yield "[REST]"
                    self.update_summary_and_messages_queue()     
            except Exception as e:
                print(f"An error occurred: {e}")     
            return 
    
    def create_message_in_db_and_update_state(self, message):
        new_message_id = str(int(time.time()))
        new_message = {
            'topics_id' : self.topic_id,
            'message_id' : new_message_id,
            'message' : message  
        }
        message_table.put_item(Item=new_message)
        Topics_table.update_item(
            Key={
                'userId': self.user_email,
                'topics_id': self.topic_id,
            },
            UpdateExpression="SET messages = list_append(messages, :i), messages_queue = list_append(messages_queue, :i), #s = :j",
            ExpressionAttributeValues={
                ':i': [new_message_id],
                ':j': self.state
            },
            ExpressionAttributeNames={
                "#s": "state",
            },
            ReturnValues="UPDATED_NEW"
        )
    
    def update_summary_and_messages_queue(self):
        # Get the current item from the table
        response = Topics_table.get_item(
            Key={
                'userId': self.user_email,
                'topics_id': self.topic_id,
            }
        )

        # Retrieve the current messages_queue
        current_messages_queue = response['Item']['messages_queue']

        # Update the message queue
        updated_messages_queue = current_messages_queue[self.len_purge_queue:]

        # Update the item in the table
        Topics_table.update_item(
            Key={
                'userId': self.user_email,
                'topics_id': self.topic_id,
            },
            UpdateExpression="SET messages_queue = :i, summary = :j",
            ExpressionAttributeValues={
                ':i': updated_messages_queue,
                ':j': self.summary
            },
            ReturnValues="UPDATED_NEW"
        )




        

    
    


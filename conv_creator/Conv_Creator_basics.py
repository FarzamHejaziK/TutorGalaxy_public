import openai
import time
import random
import os
from dotenv import load_dotenv
import time
import re
from config import user_table, conversations_table, Topics_table
import uuid
from mytiktoken import count_tokens
import time
from code_excecution.languages import langs
from code_excecution.monaco_editor_supported_langs import monaco_langs
from .chats.chatstarter_new_user import chatstarter_method
from .chats.chat_new_user import chat_new_user_method
from .analyze_conversation import analyze_conv_method 
from .create_topic import create_topic_method 
from .get_conv_details import get_conv_details_method
from .chats.chat_starter_recur_user_ver2 import chatstarter_recur_method
from .chats.chat_recur_user_ver2 import chat_recur_user_method
from .generators.generate_chat_starter_prompt import get_chatstarter_prompt_method 
from .generators.generate_chat_prompt import get_chat_prompt_method
from .finish_checker import finished_checker_method, checker_method



def concatenate_with_spaces(arr):
    result = ""
    for string in arr:
        result += string + " "
    result = result.rstrip()  # Remove trailing space
    return result

class ConvCreator_stream:
    
    ## External Methods Init
    chatstarter = chatstarter_method
    chat_new_user = chat_new_user_method
    analyze_conv = analyze_conv_method
    create_topic = create_topic_method
    get_conv_details = get_conv_details_method
    chatstarter_recurring_user = chatstarter_recur_method 
    chat_recur_user = chat_recur_user_method
    get_chatstarter_prompt = get_chatstarter_prompt_method
    get_chat_prompt = get_chat_prompt_method
    finished_checker = finished_checker_method 
    checker = checker_method


    def __init__(self, api_keys, conversation_model = 'gpt-4', extraction_model = 'gpt-4' , temperature=0.7, max_tokens=5000, conv_id = None):
        self.conv_id = conv_id
        self.api_keys = api_keys
        self.model_engine = conversation_model
        self.conversation_model = conversation_model
        self.extraction_model = extraction_model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.state = 0
        self.user_messages = []
        self.system_messages = []
        self.summary = None 
        self.message_queue = []
        self.mq_len = 15
        self.discussion = None
        self.conversation_history = []
        self.completion_token_length = 500
        self.max_token_allowed = 8000 - self.completion_token_length
        self.chat_continue_prompt_token_number = 3000 
        self.default_summary = """Summarize the conversation between 'system' and 'user'. This is the conversation: {}. 
The order of the of the conversation should remain intact. 
In your summary it should be very clear what 'system' said and what 'user' said in order. 
keep the whole summary less than {} words. 
If the text cotain the name of the 'system' or the 'user', remember to bring it in the summary intact. 
Your summay should maintain the course of conversation. Specially when the conversation took a turn.
if the system put out a plan for the conversation, bring the plan with all the details in the summary. The plan may get revised throgh the conversation
put the latest version with all the details in your summary.
User preferences is very important, if user express any prefernce bring put it in your summary. """ 




                    
    def summarizer(self, prompt):
            max_retries = 2
            retries = 0
            
            while retries <= max_retries:
                try:
                    # Randomly select an API key for each call
                    openai.api_key = random.choice(self.api_keys)
                    
                    parsed_response = openai.ChatCompletion.create(
                        model = self.extraction_model,
                        messages=[
                            {"role": "system", "content": "Summarize the conversation between 'system' and 'user'. The order of the of the conversation intact this is very importnt. In your summary it should be very clear what 'system' said and what 'user' said in order. keep the whole summary less than 3500 words. If the text cotain the name of the 'system' or the 'user', remember to bring it in the summary intact as it is very important."},
                            {"role": "user", "content": f"{prompt}"},
                        ],
                        temperature=0,
                        max_tokens=self.max_tokens 
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
    
    def handle_first_message(self, user):
        self.new_conv = self.get_user_and_topic_create_conv(user)
        self.user_given_name = user.get('given_name')
        self.user = user
        for chunk in self.process_message(""):
            yield chunk


    def handle_message(self, user_input: str, user):
        self.get_user_and_conv(user)
        self.user_given_name = user.get('given_name')
        self.user_email = user['email']
        self.user = user
        try:
            for chunk in self.process_message(user_input):
                yield chunk
        except GeneratorExit:
            print("Client disconnected.")
            # The code here will be executed if the client disconnects
            # If you want to continue the loop even after the client disconnects, you can do so
            for _ in self.process_message(user_input):
                pass  # Do nothing, just continue iterating
        self.update_and_save_records()

    def get_user_and_topic_create_conv(self, user):
        
        new_id = str(uuid.uuid4()) if not self.conv_id else self.conv_id 
        message_id = str(int(time.time()))
        user_table.update_item(
            Key={'email': user['email']},
            UpdateExpression="SET conversations = list_append(if_not_exists(conversations, :empty_list), :val1)",
            ExpressionAttributeValues={
                ':val1': [new_id],
                ':empty_list': []
            }
        )

        
        if len(user.get('created_topics',[])) == 0 or self.conv_id:
            self.state = 0
        else:
            self.state = 2
            self.user_nickname = user.get('nickname','')
            if not self.user_nickname: self.user_nickname = user.get('give_name','')

        new_conv = {
            'conv_id': new_id,
            'message_queue': [] ,
            'conversation_history': [],
            'state': self.state + 1,
        }
        return new_conv


    def get_user_and_conv(self, user):
        self.last_conv_id = user['conversations'][-1] if not self.conv_id else self.conv_id 
        self.conv = conversations_table.get_item(Key={'conv_id': self.last_conv_id})['Item']
        self.state = self.conv['state']
        self.message_queue = self.conv['message_queue']
        self.conversation_history = self.conv['conversation_history']
        return
    
    def process_message(self, user_input):
        
        full_response = []
        post_sequence_string = None


        
        if self.state in [0,2]:
            prompt = f""        
            # Consume the response from the chatstarter method  
            for chunk in self.chatstarter(prompt) if self.state == 0 else self.chatstarter_recurring_user(prompt):         
                yield chunk
                full_response.append(chunk)
            self.system_content = "".join(full_response)
            self.new_conv['message_queue'].append(f"system: {self.system_content}")
            self.new_conv['conversation_history'].append(f"system: {self.system_content}")
            conversations_table.put_item(Item=self.new_conv)
        

        if self.state in [1,3]:
            self.discussion = f"summary so far:{self.summary}, {concatenate_with_spaces(self.message_queue)}"
            ans = user_input
            self.message_queue.append(f"then user: {ans}")
            self.conversation_history.append(f"user: {ans}")
            self.conversation_so_far = concatenate_with_spaces(self.conversation_history) 
            finished_flag = self.finished_checker(self.conversation_so_far)
            prompt = f"{ans}"

            if not finished_flag:
                try:    
                    for chunk in self.chat_new_user(prompt) if self.state == 1 else self.chat_recur_user(prompt):
                        yield chunk
                        full_response.append(chunk)
                except Exception as e:
                    # Optionally log or print the error
                    print(f"An error occurred: {e}")
                    pass  # Continue after the error

                self.system_content = "".join(full_response)
                self.message_queue.append(f"then system: {self.system_content}")
                self.discussion = f"summary so far:{self.summary}, {concatenate_with_spaces(self.message_queue)}"
                self.conversation_history.append(f"system: {self.system_content}")
                prompt = f"summary so far:{self.summary}, {concatenate_with_spaces(self.message_queue)}"
                if count_tokens(concatenate_with_spaces(prompt)) + self.chat_continue_prompt_token_number >= self.max_token_allowed:
                    self.summary = self.summarizer(prompt)
                    self.message_queue = []
            
            else:
                for _ in self.handle_conv_details():
                    yield "[DONE]" 

    def handle_conv_details(self): 
        raw_conversation_info = [] 
        for chunk in self.analyze_conv():
            raw_conversation_info.append(chunk) 
            yield "[DONE]"
        raw_conversation_info = "".join(raw_conversation_info)
        self.get_conv_details(raw_conversation_info)
        
        chatstarter_prompt = []
        for chunk in self.get_chatstarter_prompt():
            chatstarter_prompt.append(chunk) 
            yield "[DONE]"
        chatstarter_prompt = "".join(chatstarter_prompt)
        
        chat_prompt = []
        for chunk in self.get_chat_prompt(chatstarter_prompt):
            chat_prompt.append(chunk) 
            yield "[DONE]"
        chat_prompt = "".join(chat_prompt)
        combined_prompt = chatstarter_prompt + "," + chat_prompt
        self.create_topic(combined_prompt)

        yield "[DONE]"  

    
    def update_and_save_records(self):
        conversations_table.update_item(
            Key={'conv_id': self.last_conv_id},
            UpdateExpression="SET conversation_history = :ch, message_queue = :mq",
            ExpressionAttributeValues={
                ':ch': self.conversation_history,
                ':mq': self.message_queue
            }
        )



            
           

        



'''
    def handle_conv(self, prompt):
        post_sequence_string = ''
        full_response = []
        found_special_sequence = False
        buffer = ""
        for chunk in self.chat_new_user(prompt) if self.state == 1 else self.chat_recur_user(prompt):
            full_response.append(chunk)

            # Append new chunks to buffer
            buffer += chunk
            
            # Process complete sequences
            while "*_*" in buffer:
                found_special_sequence = True
                before, _, after = buffer.partition("*_*")
                yield before
                buffer = after  # Update the buffer to only contain what comes after *_*

            # If no "*_*" is found but "*" or "*_" is at the end, continue to the next iteration
            if buffer.endswith("*") or buffer.endswith("*_"):
                continue

            if not found_special_sequence:
                # If "*_*" hasn't been found yet, yield the whole chunk
                yield buffer
                buffer = ""  # Clear the buffer
            else:
                yield "[DONE]"

        if found_special_sequence:
            # In case anything is left in the buffer after processing all chunks
            if buffer:
                yield buffer
            yield "finished", full_response
'''   

        


    
    


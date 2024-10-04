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






def concatenate_with_spaces(arr):
    result = ""
    for string in arr:
        result += string + " "
    result = result.rstrip()  # Remove trailing space
    return result

class TeachingAssistant_stream:
    def __init__(self, api_keys, model_engine="gpt-4", temperature=0.7, max_tokens=5000):
        self.colors = {
            'red': '\033[1;31m',
            'green': '\033[1;32m',
            'blue': '\033[1;34m',
        }
        self.api_keys = api_keys
        self.model_engine = model_engine
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.state = 0
        self.user_messages = []
        self.system_messages = []
        self.summary = None 
        self.message_queue = []
        self.mq_len = 15
        self.disscussion = None
        self.conversation_history = []
        self.chat_start_prompt = None
        self.chat_continue_prompt = None
        #self.encoding = tiktoken.encoding_for_model(model_engine)
        self.completion_token_length = 500
        self.max_token_allowed = 8000 - self.completion_token_length 



    
    def chatstarter(self, prompt):
            max_retries = 2
            retries = 0

            while retries <= max_retries:
                try:
                    '''answer = ''
                    start_time = time.time()
                    delay_time = 0.01'''
                    # Randomly select an API key for each call
                    openai.api_key = random.choice(self.api_keys)
                    
                    parsed_response = openai.ChatCompletion.create(
                        model = self.model_engine,
                        messages=[
                            {"role": "system", "content": f"{self.chat_start_prompt}"},
                            {"role": "user", "content": f"{prompt}"},
                        ],
                        temperature = self.temperature,
                        max_tokens = 1000,
                        stream = True
                    )
                    '''for event in parsed_response: 
                        # STREAM THE ANSWER
                        print(answer, end='', flush=True) # Print the response    
                        # RETRIEVE THE TEXT FROM THE RESPONSE
                        event_time = time.time() - start_time  # CALCULATE TIME DELAY BY THE EVENT
                        event_text = event['choices'][0]['delta'] # EVENT DELTA RESPONSE
                        answer = event_text.get('content', '') # RETRIEVE CONTENT
                        time.sleep(delay_time)'''
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
                    openai.api_key = random.choice(self.api_keys)
                    parsed_response = openai.ChatCompletion.create(
                        model = self.model_engine,
                        messages=[
                            {"role": "system", "content": f"{self.chat_continue_prompt}, Remember the summary of conversation so far and the your last messages are {self.disscussion}."},
                            {"role": "user", "content": f"{prompt}"},
                        ],
                        temperature=self.temperature,
                        max_tokens=500,
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
            max_retries = 2
            retries = 0
            
            while retries <= max_retries:
                try:
                    # Randomly select an API key for each call
                    openai.api_key = random.choice(self.api_keys)
                    
                    parsed_response = openai.ChatCompletion.create(
                        model = self.model_engine,
                        messages=[
                            {"role": "system", "content": "Summarize the conversation between 'system' and 'user'. The order of the of the conversation intact this is very importnt. In your summary it should be very clear what 'system' said and what 'user' said in order. keep the whole summary less than 3500 words. If the text cotain the name of the 'system' or the 'user', remember to bring it in the summary intact as it is very important."},
                            {"role": "user", "content": f"{prompt}"},
                        ],
                        temperature=self.temperature,
                        max_tokens=5000
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
        self.message_queue_ids = self.topic['messages_queue'] 
        self.create_message_queue()
        return 
    
    def create_message_queue(self):
        messages = []
        for message_id in self.message_queue_ids:
            response = message_table.get_item(
                Key={
                    'topics_id': self.topic_id,
                    'message_id': message_id,
                }
            )
            message_item = response['Item']
            messages.append(message_item['message'])
        self.message_queue = messages

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
            self.message_queue.append(self.system_content)

        elif self.state == 1:
            self.disscussion = f"summary so far:{self.summary}, {concatenate_with_spaces(self.message_queue)}"
            prompt = f"user: {user_input}"
            self.state = 1  
            self.create_message_in_db_and_update_state(prompt)
            self.message_queue.append(prompt)
            # Consume the response from the chat method
            full_response = []
            for chunk in self.chat(prompt):
                yield chunk
                full_response.append(chunk)
            
            # Set self.system_content and execute the rest of the code once the full response has been received
            self.system_content = f"{''.join(full_response)}"
            self.create_message_in_db_and_update_state(self.system_content)
            self.message_queue.append(self.system_content)
            prompt = f"summary so far:{self.summary}, {concatenate_with_spaces(self.message_queue)}"
            if count_tokens(prompt) + self.chat_continue_prompt_token_number >= self.max_token_allowed:
                self.summary = self.summarizer(prompt)
                self.message_queue = []
                self.update_summary_and_message_queue()          
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
    
    def update_summary_and_message_queue():
        Topics_table.update_item(
            Key={
                'userId': self.user_email,
                'topics_id': self.topic_id,  # replace with the actual userId
            },
            UpdateExpression="SET messages_queue = :i, summary = :j",
            ExpressionAttributeValues={
                ':i': [],  # replace with the actual new topic ID
                ':j': self.summary
            },
            ReturnValues="UPDATED_NEW"
        )



if __name__ == "__main__":
    load_dotenv()
    API_KEYS = [os.getenv("API_KEYS")]
    print("API_keys = ", API_KEYS)
    ta = TeachingAssistant(api_keys=API_KEYS, model_engine="gpt-4", temperature=1, max_tokens=5000)
    user = User.objects().first()
    if not user:
        print("No users found. Creating a new user...")
        user = User().save()
    if user:
        user_id = str(user.id)
        print(f"Using user_id: {user_id}")

        # Define test user_input and topic
        user_input = "array comrehention"
        topic = "python"
        for word in ta.handle_message(user_input, user_id, topic):
            print(word)
        

        '''# Create an asyncio event loop
        loop = asyncio.get_event_loop()

        # Use the event loop to run the handle_message function
        try:
            # Create an empty list to collect results
            result = []

            # Create an instance of the handle_message async generator
            handle_message_gen = ta.handle_message(user_input, user_id, topic)

            # Use a while loop to iterate over the handle_message generator
            while True:
                try:
                    # Use the asyncio.as_completed function to handle the async generator
                    res = loop.run_until_complete(handle_message_gen.__anext__())
                    result.append(res)
                except StopAsyncIteration:
                    # This exception is raised when the generator is exhausted
                    break

            # Print the results
            for res in result:
                print(res)
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            loop.close()'''
    
    


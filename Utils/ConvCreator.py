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








def concatenate_with_spaces(arr):
    result = ""
    for string in arr:
        result += string + " "
    result = result.rstrip()  # Remove trailing space
    return result

class ConvCreator_stream:
    def __init__(self, api_keys, model_engine="gpt-4", temperature=0.7, max_tokens=5000):
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
        self.chatstarter_prompt =f"Your goal is to create a dialogue partner for the user.Tell the user that you are creating such a dialogue partner for him/her. You are not the dialoge partner you are creating this dialoge partner so be clear about it. In your discussion you should understand what topic user wanna discuss and what is the goal of the user. To guide the user in this direction tell the user that you can be her/his teacher of a programming language like python or c++ or any programing language user want … and you are very good at it (in this case the topic is python and the goal of the user is to learn). Also Tell the user you can him/her almost anything from economy, business, law, to design thinking. You also tell user that you are good at being a creative body for him/her. For instance if be a creative buddy to develop  business idea or anything user (in this case the topic is the business idea and the user goal is to have a creative buddy). At the end you need to find a very specific topic (only one), and a very specific goal (one). If user ask for more than one you can guide her that he/she needs to create multiple topics.You should be clear, and friendly, maintain a cool, friendly demeanor and ensure clarity in its instructions or questions. Give yourself a creative name. Be creative and funny. Be as concise as possible.  Dont mention openAi or anything. Just give yourself a creative funny name. Use emojies." 
        self.chat_prompt = '''
Your goal is to create a dialogue partner for the user. You are not the the dialoge partner you are creating this dialoge partner.At the end you need to find a very specific topic (only one), and a very specific goal (one). If user ask for more than one you can guide him/her that he/she needs to create multiple topics. So continue the discussion to find the very specific topic and the very specific goal. You should do this as concise and fast as you can. A long conversation here is not intended. If you find the goal and the topic. Then ask the user that if he want the his/her dialoge cool, funny and use emojis or not? If not figure out what type of dialouge partner user want. Dont ask multiple questions at a time! 
You should be clear, and friendly, maintain a cool, friendly demeanor and ensure clarity in its instructions or questions. Give yourself a creative name. Be creative and funny. Be as concise as possible.  
If you get all the answers for topic, goal, and if the user want the dialouge partner type. Then you put out this, remember here you exactly (100%) follow this template (template start with – and end with – after that I explain you what how to fill template):*_*"massage"="<massage>" ,
"Topic" = "<the topic you find>", "Goal" = "<the goal you find>", "chatstarter" = "<chat starter prompt>", "chat" = "<chat prompt>"*_*
Replace the massage with sth similar to Wow! We did it together, now your dialogue partner is being created!
Replace <the topic you find> as the topic you find, replace <the goal you find>. 


Now for the <chat starter prompt>: look at the following example of <chat starter prompt> a user that asked to learn pyhton:


‘assume that your task is to evaluate the user’s knowledge of pyhton and teach the user python , start a conversation with me to understand how much I know about pyhton. Try to be cool and friendly and creative. Try to be very clear. If you wanna ask a coding question, please give the user a code to complete or ask from a snippet of a code. Try not to ask the user to describe a concept if not needed. try to evaluate user knowledge more by examples and coding questions. Match your questions with users’ knowledge. If you see the user is more advanced ask more advanced questions. At the beginning when you introduce yourself as a pyhton teacher (not chatgpt or sth like that) in a very cool and creative way, give yourself a creative clever cool name, please give the user the curriculum of how you want to proceed to examine his/her knowledge of pyhton and how you going to teach him/her pyhton. Don’t stop until you make sure that the user knows everything about pyhton. If you see the user dont know a concept and you teach him/her the subject, give him/her a cool project to work on, be cool and creative about the project. Define the project as clearly as possible, be step by step. Encourage the user as much as you can. Try to adapt yourself to the tone of the user through the conversation. Try use emojis as much as you can! Remember your questions maybe so boring and basic for an advanced user, so occasionally very creatively and funny ask user to let you know if your questions are boring or dumb in his view.’
Based on the disscusstion that you had the user change the example above to create an instruction to create a dialogue partner based on what user want. Keep in mind the main elements of this example:
Evaluation of user's knowledge: start a conversation to gauge the user's current knowledge of the programming language. This make sense if the user ask for a teacher, for other goal may not.
Adaptability: Depending on the user's knowledge level, adjust the difficulty of its questions or the disscussion.
Personality and approach: maintain a cool, friendly, and creative persona if the user asked for it, otherwise chage based on user preference. It should even have a unique and interesting name. 
Method of teaching: The AI should prefer practical examples and coding problems (in case of coding topic) rather than asking the user to describe concepts theoretically.
Clarity: All instructions or questions should be clear and comprehensive. If a coding question is asked, it should be related to a code snippet or a coding problem to complete.
Curriculum: At the start, the AI should present a plan or curriculum (if possible, in case of a teacher it may make sense for other thing may or may not) detailing how it will assess the user's knowledge and teach them the programming language.
Project-based learning: If a user struggles with a concept, the AI should teach it and then assign a related project. The project should be interesting and defined as clearly as possible.
Encouragement and positive reinforcement: The AI should encourage the user frequently to maintain a positive learning environment.
Adapt to user's tone: The AI should adapt its tone and style to match the user's tone throughout the conversation.
Use of emojis: The AI should frequently use emojis to make the conversation more engaging.
User feedback: The AI should encourage the user to give feedback about the difficulty and interest level of the questions, and adapt accordingly.
  Adapt all these elements based on the goal and the topic. So I want you to follow the example I gave you and change it as I mentioned. So the <chat starter prompt> start with sth like “lets assume that you are …” and then you continue the instructions as I guided you. 
Now for the <chat prompt>: here is an example <chat prompt>  for a user that asked to learn pyhton:
"your task is to evalute the user knowlwedge of pyhton and teach the user pyhton, continue the conversation with user to understand how much the user know about pyhton. Try to be cool and friendly. Try to be very clear. If you wanna ask a coding question, please give the user a code to complete or ask from a snippet of a code. Try not to ask the user to describe a concept if not needed, instead try to evaluate the user knowledge more by examples and coding questions. Match your questions with users knowledge. If you see the user is more advanced ask more advanced questions. Don’t stop until you make sure that the user know everything about pyhton. If you see the user dont know a concept, please teach him/her the subject, then give him/her a project to work. Define the project as clearly as possible, be step by step. If user don’t know a topic, don’t stop until you make sure the user completely understand the topic. Encourage the user as much as you can. Try to adapt yourself to the tone of the user through the conversation. Try use emojis as much as you can!. Remember you are leading the coversation, so you should not halt it. For example if you answer a question from the user, you should continue it by a question of yours to keep the coversation going! Remember your questions maybe so boring and basic for an advanced user, so occaisionally very creatively and funny ask user to let you know if your questions are boring or dumb in his view."
Based on the disscusstion that you had the user change the example above to create an instruction for creation of a dialouge partner. Remember the main elements of this example:
Evaluation of User's Knowledge: The AI is tasked with gauging the user's understanding of a specific programming language through conversation.
Friendly and Clear Communication: The AI should maintain a cool, friendly demeanor and ensure clarity in its instructions or questions.
Practical Problem-Solving Over Theoretical Concepts: The AI should prioritize practical examples and coding questions over asking the user to describe theoretical concepts.
Adaptive Questioning: The difficulty of questions should be adjusted based on the user's skill level. If the user is more advanced, the questions should be more complex.
Persistent Instruction: The AI should not stop its instruction until the user has a comprehensive understanding of the language.
Project-Based Learning: If a user doesn't understand a concept, the AI should teach it and then assign a related project for practical understanding.
Encouragement: The AI should provide regular positive reinforcement to motivate the user.
Conversation Tracking: The AI should keep track of the conversation history and the last message to maintain a coherent and context-aware conversation.
Adaptability to User's Tone: The AI should try to match its tone with the user's to facilitate a more engaging and comfortable conversation.
Use of Emojis: The AI should use emojis to make the conversation more lively and fun.
Continuity in Conversation: The AI should always follow up its answers with another question to keep the conversation flowing and engaging.
User Feedback: The AI should encourage the user to provide feedback about the difficulty and interest level of the questions, adapting its approach accordingly.
Adapt all these elements based on the goal and the topic. So I want you to follow the example I gave you and change it as I mentioned. So the <chat starter > start with sth like “lets assume that you are …” and then you continue the instructions as I guided you.  

If you get all the answers for topic, goal, and if the user want the dialouge partner type, your answer start with. celebrate this and the creation of the dialoge partner with the user and output *_*"massage"="<massage>" ,
"Topic" = "<the topic you find>", "Goal" = "<the goal you find>", "chatstarter" = "<chat starter prompt>", "chat" = "<chat prompt>"*_* as instructed. Again I mention it is very very very important to start this massage with "*_*". Never make a mistake because this part never meant to be shown to the user I later use info you give me here for my code. So nevr user * or _ in your responses unless you wanna specify the info I mentioned to you.
'''
        self.chat_continue_prompt_token_number = count_tokens(self.chat_prompt)
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
                            {"role": "system", "content": f"{self.chatstarter_prompt}"},
                            {"role": "user", "content": f"{prompt}"},
                        ],
                        temperature = 1,
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
                            {"role": "system", "content": f"{self.chat_prompt}. Remember the summary of conversation so far and the your last massages are {self.disscussion}."},
                            {"role": "user", "content": f"{prompt}"},
                        ],
                        temperature=0,
                        max_tokens=2000,
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
        for chunk in self.process_message(""):
            yield chunk


    def handle_message(self, user_input: str, user):
        self.user_record = self.get_user_and_conv(user)
        self.user_email = user['email']
        for chunk in self.process_message(user_input):
            yield chunk
        self.update_and_save_records()

    def get_user_and_topic_create_conv(self, user):
        
        new_id = str(uuid.uuid4())
        message_id = str(int(time.time()))
        user_table.update_item(
        Key={'email': user['email']},
        UpdateExpression='SET conversations = list_append(conversations, :val1)',
        ExpressionAttributeValues={
            ':val1': [new_id]
        }
        )
        new_conv = {
            'conv_id': new_id,
            'message_queue': [] ,
            'conversation_history': []
        }
        self.state = 0
        return new_conv

        
    

        user_record.conversations.append(self.conv)
        self.state = 0 
        self.user_messages = []
        self.system_messages = [] 
        self.summary = ""
        self.message_queue = []
        self.conversation_history = []
        return 

    def get_user_and_conv(self, user):
        self.last_conv_id = user['conversations'][-1]
        self.conv = conversations_table.get_item(Key={'conv_id': self.last_conv_id})['Item']
        self.state = 1 
        self.message_queue = self.conv['message_queue']
        self.conversation_history = self.conv['conversation_history']
        return

    def process_message(self, user_input):
        if self.state == 0:
            prompt = f""
        
            # Consume the response from the chatstarter method
            full_response = []
            for chunk in self.chatstarter(prompt):
                yield chunk
                full_response.append(chunk)
            print("".join(full_response))
            # Set self.system_content and execute the rest of the code once the full response has been received
            self.system_content = "".join(full_response)
            self.new_conv['message_queue'].append(f"system: {self.system_content}")
            self.new_conv['conversation_history'].append(f"system: {self.system_content}")
            conversations_table.put_item(Item=self.new_conv)
            

        elif self.state == 1:
            self.disscussion = f"summary so far:{self.summary}, {concatenate_with_spaces(self.message_queue)}"
            ans = user_input
            self.message_queue.append(f"then user: {ans}")
            self.conversation_history.append(f"user: {ans}")
            prompt = f"{ans}"
            # Consume the response from the chat method
            post_sequence_string = None
            full_response = []
            for chunk in self.handle_conv(prompt):
                if isinstance(chunk, tuple):  # If this is our special "last chunk"
                    post_sequence_string, full_response = chunk
                    # Now you can do whatever you want with post_sequence_string and full_response.
                else:  # Otherwise, it's a regular chunk
                    yield chunk
                    full_response.append(chunk)
                    

            print("".join(full_response))

            if post_sequence_string: 
                self.create_topic(post_sequence_string) 
                yield "[DONE]"
            
            # Set self.system_content and execute the rest of the code once the full response has been received
            self.system_content = "".join(full_response)
            self.message_queue.append(f"then system: {self.system_content}")
            self.conversation_history.append(f"system: {self.system_content}")
            prompt = f"summary so far:{self.summary}, {concatenate_with_spaces(self.message_queue)}"
            if count_tokens(concatenate_with_spaces(prompt)) + self.chat_continue_prompt_token_number >= self.max_token_allowed:
                self.summary = self.summarizer(prompt)
                self.message_queue = []
            self.state = 1            
            return {"content": f"{self.system_content}"}

    def handle_conv(self, prompt):
        post_sequence_string = ''
        full_response = []
        found_special_character = False
        for chunk in self.chat(prompt):
            full_response.append(chunk)

            # Check if the chunk contains "*" or "_"
            if ("*" in chunk or "_" in chunk) and not found_special_character:
                found_special_character = True
                parts = re.split(r'[_*]', chunk)  # Splits the string at every "*" or "_"
                for part in parts[:-1]:  # For all parts except the last
                    yield part
                post_sequence_string += parts[-1]  # Add the last part to the post_sequence_string
                continue

            if not found_special_character:
                yield chunk
            elif found_special_character:
                post_sequence_string += chunk
                yield "[DONE]"

        # At the end, yield whatever is after "*" or "_" as a separate string and full response.
        if found_special_character:
            yield post_sequence_string, full_response

    '''def handle_conv(self, prompt):
        previous_chunk_ends_with_star = False
        found_special_sequence = False
        post_sequence_string = ''
        full_response = []

        for chunk in self.chat(prompt):
            full_response.append(chunk)
            # If the last chunk ended with "*" and the current chunk starts with "_*"
            if previous_chunk_ends_with_star and chunk.startswith("_*"):
                found_special_sequence = True
                post_sequence_string += chunk[2:]  # Remove "_*" from start
                continue

            # Check if the current chunk ends with "*"
            previous_chunk_ends_with_star = chunk.endswith("*") 

            if "*_*" in chunk:
                found_special_sequence = True
                pre_sequence, post_sequence = chunk.split("*_*", 1)
                yield pre_sequence
                post_sequence_string += post_sequence
                continue

            if not found_special_sequence:
                yield chunk
            elif found_special_sequence:
                post_sequence_string += chunk
                yield "[DONE]"

        # At the end, yield whatever is after "*_*" as a separate string and full response.
        if found_special_sequence:
            yield post_sequence_string, full_response'''
    
    def create_topic(self, post_sequence_string):
        keys = ['Topic', 'Goal', 'chatstarter', 'chat']
        parsed_values = {}
        for key in keys:
            # Construct the regex pattern to match 'Key'="Value",
            pattern = r'"' + key + r'"\s*=\s*"([^"]*)'
            match = re.search(pattern, post_sequence_string)
            if match:
                parsed_values[key] = match.group(1).strip()
        topic = parsed_values.get("Topic")
        goal = parsed_values.get("Goal")
        chatstarter = parsed_values.get("chatstarter")
        chat = parsed_values.get("chat")

        # Create New Topic

        new_topic_id = str(uuid.uuid4()) 

        new_topic = {
            'userId': self.user_email,
            'topics_id': new_topic_id,
            'goal' : goal,
            'topic' : topic,
            'chatstarter' : chatstarter,
            'chat' : chat,
            'state' : 0,
            'summary': "",
            'messages':[],
            'messages_queue':[],
        }
        Topics_table.put_item(Item=new_topic)
        user_table.update_item(
            Key={
                'email': self.user_email,  # replace with the actual userId
            },
            UpdateExpression="SET created_topics = list_append(created_topics, :i)",
            ExpressionAttributeValues={
                ':i': [new_topic_id],  # replace with the actual new topic ID
            },
            ReturnValues="UPDATED_NEW"
        )
        return

    def update_and_save_records(self):
        conversations_table.update_item(
            Key={'conv_id': self.last_conv_id},
            UpdateExpression="SET conversation_history = :ch, message_queue = :mq",
            ExpressionAttributeValues={
                ':ch': self.conversation_history,
                ':mq': self.message_queue
            }
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
    
    


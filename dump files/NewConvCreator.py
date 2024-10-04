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
        self.discussion = None
        self.chatstarter_temperature = 0.3
        self.chatstarter_recurring_user_temperature = 0.3
        self.chat_temperature = 0.3
        self.conversation_history = []
        self.chatstarter_prompt ='''
        Your goal is to create a dialogue buddy for the user. You are not the dialogue buddy, you are the one who creates it. So introduce yourself as a wizard to create a buddy. 
        To guide the user in this direction tell the user that you can be her/his teacher (mention the word "teacher" explictly) of a programming language like python, javascript, HTML or any programing language user want 
        and you are very good at it.
        Also Tell the user you can teach them almost anything from economy, business, law, to design thinking or whatever user want. 
        You also tell user that you are good at being a creative buddy for him/her. For instance if be a creative buddy to develop business idea or any idea user wants.
        If user ask for more than one topic and goal you can guide her that he/she needs to create multiple topics.
        You should be very clear, straight forward and ensure clarity in its instructions or questions. Dont use complicated words.
        keep things as simple as possible.
        Be as concise as possible. Dont mention openAi or anything. Use emojies.'''

        self.chatstarter_recurring_user_prompt = '''
        Your goal is to create a dialogue buddy for the user. You are not the dialogue buddy, you are the one who creates it. 
        you previously introduced yourself to the user. So in a cool way tell the user that you already introduced yourself to the user and he/she know you. but if the user wants you can introduce yourself again.
        Then ask the user what specific topic he/she has in in mind.  
        Be as concise as possible. Dont mention openAi or anything. Use emojies.'''
        
        
        
        self.chat_prompt = '''
        Your goal is to create a dialogue buddy for the user. You are not the the dialoge buddy you are creating this dialoge buddy.At the end you need to find a very specific topic (only one), and a very specific goal (one).
        If user ask for more than one you can guide him/her that he/she needs to create multiple topics. So continue the discussion to find the very specific topic and the very specific goal. 
        You should do this as concise and fast as you can. A long conversation here is not intended. If you find the goal and the topic. Then you should find the user preferences about his dialouge buddy, for isntance if the user want the his/her dialoge cool, funny and use emojis or any other preferences? (be creative here besed on the conversation) If not figure out what type of dialouge buddy user want.
        Dont ask multiple questions at a time! 
        You should be clear, and friendly, maintain a cool, friendly demeanor and ensure clarity in its instructions or questions. Be creative and funny. Be as concise as possible.  
        If you get all the answers for topic, goal, and if the user want the dialouge buddy type. Then celebrate this with the user and end the conversation. And the end of your massage add "*_* *_*" so the user can understand the discusstion is finished.
        if the user asks you to introduce yourself:
        introduce yourself as a wizard to create a buddy. 
        To guide the user in this direction tell the user that you can be her/his teacher (mention the word "teacher" explictly) of a programming language like python, javascript, HTML or any programing language user want 
        and you are very good at it.
        Also Tell the user you can teach them almost anything from economy, business, law, to design thinking or whatever user may want. 
        You also tell user that you are good at being a creative buddy for him/her. For instance if be a creative buddy to develop business idea or any idea user wants.
        '''
        
        self.chat_continue_prompt_token_number = count_tokens(self.chat_prompt)
        self.completion_token_length = 500
        self.max_token_allowed = 8000 - self.completion_token_length 



    def get_topic_and_goal_and_lang(self):
        max_retries = 2
        retries = 0
        prompt = f"""This is a conversation between the user and thesystem: {self.discussion}. In this conversation user defined a goal and a topic.
        please extract them from the discussion.
        This is a list of programing languages with their {langs}. If the goal and topics of the conversation is about one of these languages, extract the id and the name of the languages (call it lang_name). 
        if the user ask for something that is not directly in the list but is part of the langugaues in the list choose that language (for instance if the user ask for Pandas, you choose Python for ML (3.11.2), ID = 25, and extract the name as Python and ID as 23). 
        Now when are gonna find monaco_name, look at {monaco_langs} and find a name in this list that matches the name of languages (for instace for C# (Mono 6.12.0.122), ID = 22 the monaco_name is csharp, for Python for ML (3.7.7), ID = 10 the monaco_name is python). 
        The id should be the most related and the most recent version of the programming languages. 
        If the the conversation is not about a programming language or the programming language is not in the list, the id is -1 and the lang_name is -1.
        if you could not find a proper match for monaco_name then assume it is -1.  
        Then give me the topic and the goal and the id and the lang_name in this format:
        "topic":"<your extracted topic>", "goal":"<your extracted goal>", "langid":"<your extracted id>" , "lang_name":"<your extracted lang_name>", "monaco_name":"<your extracted monaco_name>" ."""

        while retries <= max_retries:
            try:
                openai.api_key = random.choice(self.api_keys)
                
                parsed_response = openai.ChatCompletion.create(
                    model = self.model_engine,
                    messages=[
                        {"role": "system", "content": f"{prompt}"},
                    ],
                    temperature = 0,
                    max_tokens = 1000,
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
    
    def get_chatstarter_prompt(self):
        max_retries = 2
        retries = 0
        prompt = f"""your goal is to ctreate an instruction for a chatbot based on the user topic and goal. Here is an example of such instruction for a user that wanna learn python:
        "assume that your task is to evaluate the user’s knowledge of pyhton and teach the user python,
        start a conversation with me to understand how much I know about pyhton. Try to be cool and friendly and creative.
        Try to be very clear. If you wanna ask a coding question, please give the user a code to complete or ask from a snippet of a code.
        Try not to ask the user to describe a concept if not needed. try to evaluate user knowledge more by examples and coding questions.
        Match your questions with users’ knowledge. If you see the user is more advanced ask more advanced questions.
        At the beginning when you introduce yourself as a pyhton teacher (not chatgpt or sth like that) in a very cool and creative way,
        give yourself a creative clever cool name, please give the user the curriculum of how you want to proceed to examine his/her knowledge of pyhton and how you going to teach him/her pyhton.
        Don’t stop until you make sure that the user knows everything about pyhton.
        If you see the user dont know a concept and you teach him/her the subject, give him/her a cool project to work on, be cool and creative about the project.
        Define the project as clearly as possible, be step by step. Encourage the user as much as you can.
        Try to adapt yourself to the tone of the user through the conversation.
        Try use emojis as much as you can! Remember your questions maybe so boring and basic for an advanced user, so occasionally very creatively and funny ask user to let you know if your questions are boring or dumb in his view."
        The main elements tha should be included in your instruction:
        0-Starting the conversation: your instruction should guide the bot to start the conversation.
        1-Evaluation of user's knowledge: start a conversation to gauge the user's current knowledge of the programming language. This make sense if the user asked for learning sth.
        2-Adaptability: Depending on the user's knowledge level, adjust the difficulty of its questions or the disscussion.
        3-Personality and approach: the user asked for a cool, friendly, and creative persona and instruction follow this. Your instruction should follow user preferences. It should also instruct the bot to give himself a unique and interesting name.
        4-Method of teaching: The AI should prefer practical examples and coding problems (in case of coding topic) rather than asking the user to describe concepts theoretically.
        5-Clarity: All instructions or questions should be clear and comprehensive.
        6-Planning: Planning is very improtant if user asked to learn sth or be prepared sth or anything that needs planning. At the start, the isntrction should instrut the bot to create a plan or curriculum if possible.
        7-Project-based learning: the instrcution should guide the bot to see when user struggles with a concept, the bot should teach it and then assign a related project. The project should be interesting and defined as clearly as possible.
        8-Encouragement and positive reinforcement
        9-Adapt to user's tone: The instruction should instruct the bot to adapt its tone and style to match the user's tone throughout the conversation.
        10-Use of emojis: In case user asked for it.
        11-User feedback: the instruction should guide the bot to encourage the user to give feedback about the difficulty and interest level of the questions, and adapt accordingly.
        12-name: the instruction should guide the chatbot to give itself a name.
       
        Now this is a conversation between the user and the system: {self.discussion}. Whats important here is what user want. So Based on user preferences create the instruction.
        Then give me the instruction in this format: "chatstarter":"<your instruction>" ."""



        while retries <= max_retries:
            try:
                openai.api_key = random.choice(self.api_keys)
                
                parsed_response = openai.ChatCompletion.create(
                    model = self.model_engine,
                    messages=[
                        {"role": "system", "content": f"{prompt}"},
                    ],
                    temperature = 0,
                    max_tokens = 1000,
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


    def get_chat_prompt(self,chat_prompt):
        max_retries = 2
        retries = 0
        prompt = f""" look at this instruction: {chat_prompt}. Do the follwoing changes to it:
        1 - change start to continue. 
        2 - remove the part related to planning. 
        3 - remove the part related giving itself a name or intoducing itself.
        4 - add this to the istruction: if user ask a question. It is a sign of user interest in the topic so try to comprehensively cover that topic.
        5 - add this to the istruction: keep the flow and consistensy of the discussion in short trem and long term. 
            For the long-term consistency it is very important to refer to the conversation and see if system put out a plan 
            (this plan normally come at the begining of the conversation and may be revised throughout the conversation) 
            for the conversation and follow this master plan throughout the conversation.  
       
        keep all other elements the same. 
        Then give me the instruction in this format: "chat":"<your instruction>" ."""



        while retries <= max_retries:
            try:
                openai.api_key = random.choice(self.api_keys)
                
                parsed_response = openai.ChatCompletion.create(
                    model = self.model_engine,
                    messages=[
                        {"role": "system", "content": f"{prompt}"},
                    ],
                    temperature = 0,
                    max_tokens = 1000,
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

    def chatstarter(self, prompt):
            max_retries = 2
            retries = 0

            while retries <= max_retries:
                try:
                    openai.api_key = random.choice(self.api_keys)
                    
                    parsed_response = openai.ChatCompletion.create(
                        model = self.model_engine,
                        messages=[
                            {"role": "system", "content": f"{self.chatstarter_prompt}"},
                            {"role": "user", "content": f"{prompt}"},
                        ],
                        temperature = self.chatstarter_temperature,
                        max_tokens = 1000,
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

    def chatstarter_recurring_user(self, prompt):
            max_retries = 2
            retries = 0

            while retries <= max_retries:
                try:
                    openai.api_key = random.choice(self.api_keys)
                    
                    parsed_response = openai.ChatCompletion.create(
                        model = self.model_engine,
                        messages=[
                            {"role": "system", "content": f"{self.chatstarter_recurring_user_prompt}"},
                            {"role": "user", "content": f"{prompt}"},
                        ],
                        temperature = self.chatstarter_recurring_user_temperature,
                        max_tokens = 1000,
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
                    openai.api_key = random.choice(self.api_keys)
                    parsed_response = openai.ChatCompletion.create(
                        model = self.model_engine,
                        messages=[
                            {"role": "system", "content": f"{self.chat_prompt}. Remember you already started the conversation (you are the system) and the summary of conversation so far and the your last massages are {self.discussion}."},
                            {"role": "user", "content": f"{prompt}"},
                        ],
                        temperature=self.chat_temperature,
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
        for chunk in self.process_message(""):
            yield chunk


    def handle_message(self, user_input: str, user):
        self.user_record = self.get_user_and_conv(user)
        self.user_email = user['email']
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
        if len(user['created_topics']) == 0:
            self.state = 0
        else:
            self.state = 0.5
        return new_conv


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
            #print("".join(full_response))
            # Set self.system_content and execute the rest of the code once the full response has been received
            self.system_content = "".join(full_response)
            self.new_conv['message_queue'].append(f"system: {self.system_content}")
            self.new_conv['conversation_history'].append(f"system: {self.system_content}")
            conversations_table.put_item(Item=self.new_conv)
        
        if self.state == 0.5:
            prompt = f""
        
            # Consume the response from the chatstarter method
            full_response = []
            for chunk in self.chatstarter_recurring_user(prompt):
                yield chunk
                full_response.append(chunk)
            #print("".join(full_response))
            # Set self.system_content and execute the rest of the code once the full response has been received
            self.system_content = "".join(full_response)
            self.new_conv['message_queue'].append(f"system: {self.system_content}")
            self.new_conv['conversation_history'].append(f"system: {self.system_content}")
            conversations_table.put_item(Item=self.new_conv)
            

        elif self.state == 1:
            self.discussion = f"summary so far:{self.summary}, {concatenate_with_spaces(self.message_queue)}"
            ans = user_input
            self.message_queue.append(f"then user: {ans}")
            self.conversation_history.append(f"user: {ans}")
            prompt = f"{ans}"
            # Consume the response from the chat method
            post_sequence_string = None
            full_response = []
            try:
                for chunk in self.handle_conv(prompt):
                    if isinstance(chunk, tuple):  # If this is our special "last chunk"
                        post_sequence_string, full_response = chunk
                        # Now you can do whatever you want with post_sequence_string and full_response.
                    else:  # Otherwise, it's a regular chunk
                        yield chunk
                        full_response.append(chunk)
            except Exception as e:
                # Optionally log or print the error
                print(f"An error occurred: {e}")
                pass  # Continue after the error

                    

            #print("".join(full_response))

            
            
            # Set self.system_content and execute the rest of the code once the full response has been received
            self.system_content = "".join(full_response)
            self.message_queue.append(f"then system: {self.system_content}")
            self.discussion = f"summary so far:{self.summary}, {concatenate_with_spaces(self.message_queue)}"
            # get topic and goal 
            if post_sequence_string:
                
                # create goal and topic
                goal_and_topic_and_lang = [] 
                for chunk in self.get_topic_and_goal_and_lang():
                    goal_and_topic_and_lang.append(chunk) 
                    yield "[DONE]"
                goal_and_topic_and_lang = "".join(goal_and_topic_and_lang)
                print(goal_and_topic_and_lang)
                
                # create chat starter prompt
                chatstarter_prompt = []
                for chunk in self.get_chatstarter_prompt():
                    chatstarter_prompt.append(chunk) 
                    yield "[DONE]"
                chatstarter_prompt = "".join(chatstarter_prompt)
                #print(chatstarter_prompt) 

                # create chat  prompt
                chat_prompt = []
                for chunk in self.get_chat_prompt(chatstarter_prompt):
                    chat_prompt.append(chunk) 
                    yield "[DONE]"
                chat_prompt = "".join(chat_prompt)
                #print(chat_prompt)
                combined_prompt = goal_and_topic_and_lang + "," + chatstarter_prompt + "," + chat_prompt
                self.create_topic(combined_prompt)
                yield "[DONE]" 

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
                yield "[DONE]"
        
        if found_special_character:
            #print("I am here")
            #print("post_sequence_string",post_sequence_string)
            yield "finished", full_response


    def create_topic(self, post_sequence_string):
        keys = ['topic', 'goal', 'chatstarter', 'chat','langid','lang_name','monaco_name']
        parsed_values = {}
        #print("input", post_sequence_string)
        for key in keys:
            # Construct the regex pattern to match 'Key'="Value",
            pattern = r'"' + key + r'"\s*:\s*"([^"]*)'
            match = re.search(pattern, post_sequence_string)
            if match:
                parsed_values[key] = match.group(1).strip()
        topic = parsed_values.get("topic")
        goal = parsed_values.get("goal")
        chatstarter = parsed_values.get("chatstarter")
        chat = parsed_values.get("chat")
        langid = parsed_values.get("langid")
        langname = parsed_values.get("lang_name")
        monaconame = parsed_values.get("monaco_name")


        new_topic_id = str(uuid.uuid4()) 

        new_topic = {
            'userId': self.user_email,
            'topics_id': new_topic_id,
            'goal' : goal,
            'topic' : topic,
            'chatstarter' : chatstarter,
            'chat' : chat,
            'langid' : langid,
            'lang_name' : langname,
            'monaco_name': monaconame,
            'text_editor_used' : 0,
            'code_editor_used' : 0,
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
        


    
    


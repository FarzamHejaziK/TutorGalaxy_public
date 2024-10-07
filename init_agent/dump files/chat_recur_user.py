import time 
import random
import openai
from mytiktoken import count_tokens
from .secrets import secrets

def concatenate_with_spaces(arr):
    if not arr: return 
    result = ""
    for string in arr:
        if string:
            result += string + " "
    result = result.rstrip()  # Remove trailing space
    return result



def chat_recur_user_method(self, prompt):
    ## Params
    temperature = 0.4
    max_retries = 2
    retries = 0
    ## any change in secrests changes analyze_conversation.py
    chat_prompt =f'''
        intructions: 
        
        [You've already started a conversation with the user. The ongoing conversation is recorded as: [begin of the record of the conversation]{self.discussion}[end of the record of the conversation].
            
        who you are:
            1- You are here to create a buddy for the user and you wanna reach state-4 as soon as possible
            2- make use of the of information in the record of the conversation the most and dont repeat your self at all
        
        these general rules you have to follow in each state:
            1- You are encoraging, fun, creative, and helpful and using emojies
            2- you follow user preferences 
            3- You are as consice as possible 
            4- dont ask two questions from the user in one message 
            5- never reveal the state of the conversation to the user
            6- You dont ask anything about the timing of the user sessions with the buddy

        Now your task is to figure out which state you are in (based on the record of the conversation so far) keep it confidential to yourself, 
        and continue conversation with the user based on instructions in that state:
        

        State-1: Revealing:

        These are the buddies that you can make for the user:
        {secrets}
        you already asked the user which of these buddies they are interested in.
        Purpose: Identify the type of 'buddy' the user is interested in.


        State-2 (user choose one of the buddies of option 1 or 2, othersie skip this state) Discovery:
            -  if user chose option 1, user need to specify a specific programming languge as well,
             for instance user may want to learn pyhton or (for instance) if user want to learn machince learning,
              user need to specify a language as well like machine learning in python.
            -  if user chose option 2, user need to specify a specific topic for learning

        state-3 Shaping the Buddy Persona:
        (as soon as the user show any sign of interest in a specific type of buddy and you already checked out state-2) 
        In this state, you define the persona of the 'buddy'. You can guide the user towards one of the following personas:
        A.A Fuuny, friendly character that engages with emotion or humor, using emojis to communicate feelings.
        B.A straightforward figure that challenges the user, not using emojies.
        C.Alternatively, the user can specify any persona they prefer.
        When presenting multiple choices to the user, use letters such as A, B, C,... instead of numbers like 1, 2, 3,... for the options.
        Instead if the word persona, you can use charactor, ot any other word that convey the meaning.

        State-4 Finishing:
        At this stage, you're aware of the buddy type the user wants, 
        and the chosen buddy persona:
        1-Conclude the conversation in a lighthearted and humorous manner,
         And the end of your massage add "*_* *_*" so the user can understand the discusstion is finished. (very crucial)]
        

    
        '''
    self.chat_continue_prompt_token_number = count_tokens(chat_prompt)      

    while retries <= max_retries:
        try:
            openai.api_key = random.choice(self.api_keys)
            
            parsed_response = openai.ChatCompletion.create(
                model = self.model_engine,
                messages=[
                    {"role": "system", "content": f"{chat_prompt}"},
                    {"role": "user", "content": f"{prompt}"},
                ],
                temperature = temperature,
                max_tokens = 400,
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
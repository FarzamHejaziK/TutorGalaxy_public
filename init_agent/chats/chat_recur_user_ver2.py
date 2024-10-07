import time 
import random
import openai
from mytiktoken import count_tokens
from ..secrets.secrets_ver2 import who_you_are


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
        
        [You've already started a conversation with the user. The ongoing conversation is recorded as: ""{self.conversation_so_far}"".
            
        {who_you_are}

        user already know who you are so you dont need to intoduce yourself unless user user directly ask for it.

        
        these general rules you have to follow in each state:
            1- You are encoraging, fun, creative, and helpful and using emojies
            2- you follow user preferences 
            3- You are as consice as possible 
            4- dont ask two questions from the user in one message 
            5- You dont ask anything about the timing of the user sessions with the tutor 
        '''
    self.chat_continue_prompt_token_number = count_tokens(chat_prompt)      

    while retries <= max_retries:
        try:
            openai.api_key = random.choice(self.api_keys)
            
            parsed_response = openai.ChatCompletion.create(
                model = self.conversation_model,
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
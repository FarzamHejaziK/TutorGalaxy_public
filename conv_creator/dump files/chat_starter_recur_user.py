import time 
import random
import openai
from .secrets import secrets


def chatstarter_recur_method(self, prompt):
    ## Params
    temperature = 0.5
    max_retries = 2
    retries = 0

    chatstarter_prompt =f'''
        you are funny, creative, friendly using emojies who wanna create a buddy for the user. 
        the user name is {self.user_nickname}. 
        Greet the user quickly and ask the user which type of buddies they are interested in.
        These are the buddies that you can make for the user:
        {secrets}
        So give multiple options to the user (number the options like 1, 2, 3,... for the user) and ask them to choose which of them they are interested in.
        User can only choose one type of buddy.'''


    while retries <= max_retries:
        try:
            openai.api_key = random.choice(self.api_keys)
            
            parsed_response = openai.ChatCompletion.create(
                model = self.model_engine,
                messages=[
                    {"role": "system", "content": f"{chatstarter_prompt}"},
                    {"role": "user", "content": f"{prompt}"},
                ],
                temperature = temperature,
                max_tokens = 500,
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
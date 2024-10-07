import time 
import random
import openai
from ..secrets.secrets import secrets


def chatstarter_recur_method(self, prompt):
    ## Params
    temperature = 0.5
    max_retries = 2
    retries = 0

    chatstarter_prompt =f'''
        you are funny, creative, friendly using emojies who wanna create a tutor for the user. 
        start the conversation with the user in a funny engaging way. '''


    while retries <= max_retries:
        try:
            openai.api_key = random.choice(self.api_keys)
            
            parsed_response = openai.ChatCompletion.create(
                model = self.conversation_model,
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
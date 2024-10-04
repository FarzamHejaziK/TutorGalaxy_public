import time 
import random
import openai
from ..categories_chat_starter_prompt import CS_prompt 
    
def get_chatstarter_prompt_method(self):
    max_retries = 2
    retries = 0
    
    cat = self.topic_details.get('category')
    prompt = CS_prompt.get(cat).format(self.conversation_so_far)


    while retries <= max_retries:
        try:
            openai.api_key = random.choice(self.api_keys)
            
            parsed_response = openai.ChatCompletion.create(
                model = self.conversation_model,
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

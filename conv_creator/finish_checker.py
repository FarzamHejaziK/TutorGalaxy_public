import re
import time 
import random
import openai
from .secrets.secrets_ver2 import who_you_are

def finished_checker_method(self,content):


    prompt = f""" This is conversation between the user and the system: [begin] {content} [end].
            This is the instruction for the system:(how the system supposed to behave)
            [begin]
            {who_you_are}
        user already know who you are so you dont need to intoduce yourself unless user user directly ask for it.

        
        these general rules you have to follow in each state:
            1- You are encoraging, fun, creative, and helpful and using emojies
            2- you follow user preferences 
            3- You are as consice as possible 
            4- dont ask two questions from the user in one message 
            5- You dont ask anything about the timing of the user sessions with the tutor 
            [end]

            "Task Instructions":
            "check" the conversation to determine if the user has specified all these three "features":
            -The topic they wish to learn.
            -The persona or character of the tutor.
            -the behaviour of the tutor as defined in "Tutor Bahaviour"

        Then, provide your findings in the format below, True if user specified all the three "features" and False otherwise:
        "check": "True" or "False"      
    """
    #print("covered Prompt", prompt)
    max_retries = len(self.api_keys)+2
    retries = 0
    while retries <= max_retries:
        try:
            # Randomly select an API key for each call
            openai.api_key = self.api_keys[retries % len(self.api_keys)]
            parsed_response = openai.ChatCompletion.create(
                model = self.extraction_model,
                messages=[
                    {"role": "system", "content":prompt},
                ],
                temperature = 0,
                max_tokens = 50
            )
            content = parsed_response["choices"][0]["message"]["content"]
            return self.checker(content) == 'True'
        except Exception as e:
            print(f"Error in chat method: {e}")
            retries += 1
            if retries <= max_retries:
                print("Retrying with a new API key...")
                time.sleep(1)
            else:
                return "Sorry, there was an issue connecting to the API. Please try again later."


def checker_method(self,content):
    keys = ['check']
    parsed_values = {}
    #print("input", post_sequence_string)
    for key in keys:
        # Construct the regex pattern to match 'Key'="Value",
        pattern = r'"' + key + r'"\s*:\s*"([^"]*)'
        match = re.search(pattern, content)
        if match:
            parsed_values[key] = match.group(1).strip()
    return parsed_values.get("check")

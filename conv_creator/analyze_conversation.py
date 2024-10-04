import time 
import random
import openai
from code_excecution.languages import langs
from code_excecution.monaco_editor_supported_langs import monaco_langs
from .secrets.secrets import secrets


def analyze_conv_method(self):
    max_retries = 2
    retries = 0
    prompt = f"""This is a conversation between the user and the system: [begin]{self.conversation_so_far}[end]. 

    Your task is to analyse this conversation and output some info about it in a specefic format:

    1- Category: Please determine which category of buddy the user choose from the following list:
        {secrets}

    if user want to learn anything related to a computer science topic the category is 1.
    if user want to learn anything excluding computer science topics the category is 2.

    here you only extract a number in the interval 1 to maximum number of options in the list.

    2- topic and goal: 
    if category in between 1 to 3:
    what user asked for (summerize in a an informative topic) in less than 4 words.
    goal a more descriptive topic for wahy user want in less than 12 words. 
    the topic should be the main thing user want for example if user wanna learn pyhton, the topic is python and the goal is learning.
    or user may ask for a certain type of buddy. 

    3- programing language: This is a list of programing languages with their {langs}. If the goal and topics of the conversation 
    is about one of these languages, extract the id and the name of the languages (call it lang_name). 
    if the user ask for something that is not directly in the list but is part of the langugaues
    in the list choose that language (for instance if the user ask for Pandas, you choose Python for ML (3.11.2), ID = 25, and extract the name as Python and ID as 23)
    (if you have mutiple versions to choose, choose the latest). 
    If the the conversation is not about a programming language or the programming language is not in the list, the id is -1 and the lang_name is -1.
    
    4-Monaco name: look at {monaco_langs} and find a name in this list that matches the name of languages (for instace for C# (Mono 6.12.0.122), ID = 22 the monaco_name is csharp, for Python for ML (3.7.7), ID = 10 the monaco_name is python). 
    The id should be the most related and the most recent version of the programming languages. 
    if you could not find a proper match for monaco_name then assume it is -1.

    5- nickname: if the user identify a nickname, extract it. If the system call user with a name that not count as the user nickname. if you cant find a nickname return -1.

    6- persona_pref: user prefernce for tutor persona with all the details. 

    7- tutor_bahaviour: user prefernce for tutor bahavior (if user asked for a mixed of the two following option choose 1):
        1. A structured tutor who designs and follows a comprehensive course plan tailored to the topic you've chosen and then teach you the course and then stays with you till the end.
        2. A responsive tutor who focuses solely on answering your questions about the topic.

          
    Then output the extracted info in the following format:
    "topic":"<your extracted topic>",
    "goal":"<your extracted goal>",
    "langid":"<your extracted id>",
    "lang_name":"<your extracted lang_name>",
    "monaco_name":"<your extracted monaco_name>",
    "nickname":"<your extracted nickname>",
    "category":"<your extracted category>",
    "persona_pref":"<your extracted persona_pref>",
    "tutor_bahaviour": "<1 or 2>"
    ."""
    while retries <= max_retries:
        try:
            openai.api_key = self.api_keys[retries % len(self.api_keys)]
            
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
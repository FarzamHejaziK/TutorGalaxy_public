
from config import *
from mytiktoken import *
import threading
import re
import time 
import random
import openai

def concatenate_with_spaces(arr):
    result = ""
    for string in arr:
        result += string + " "
    result = result.rstrip()  # Remove trailing space
    return result


def process_message_QA_method(self, user_input):

    if self.state == 0:
        prompt = f""
    
        # Consume the response from the chatstarter method
        full_response = []
        for chunk in self.chatstarter(prompt):
            yield chunk
            full_response.append(chunk)
        
        full_response = []

        #self.tempplan = False
        for buffered_chunk in self.chat_QA(prompt):
            yield buffered_chunk
            full_response.append(buffered_chunk)

        
        # Set self.system_content and execute the rest of the code once the full response has been received
        self.system_content = f"system: {''.join(full_response)}"

        self.state = 1
        self.create_message_in_db_and_update_state(self.system_content)
        self.messages_queue.append(self.system_content)

    elif self.state == 1:
        self.discussion = f"summary so far:{self.summary}, {concatenate_with_spaces(self.messages_queue)}"
        prompt = f"user: {user_input}"
        self.state = 1  
        self.create_message_in_db_and_update_state(prompt)
        self.messages_queue.append(prompt)

    # Consume the response from the chat method
    full_response = []

    
    for chunk in self.process_with_plan(user_input,next_step):
        yield chunk
        full_response.append(chunk)


    # Set self.system_content and execute the rest of the code once the full response has been received
    self.system_content = f"{''.join(full_response)}"
    if not self.system_content.startswith('system:'):
        self.system_content = f'system: {self.system_content}'


    self.create_message_in_db_and_update_state(self.system_content)
    self.messages_queue.append(self.system_content)
    self.find_last_covered(''.join(full_response))

    return

def process_with_plan_method(self, user_input,next_step):

    user_prefer = self.topic.get('user_prefer','')
    who_you_are = self.topic['who_you_are']
    last_10_messages = concatenate_with_spaces(self.messages_queue[-10:])
    covered_topics = concatenate_with_spaces(self.covered_arr_to_set(self.topic.get('topics_covered',['0'])))
    print("Whats covered:", covered_topics)
    math_prompt = r"""Here's how you should format mathematical formulas according to the instruction provided:
1. For inline mathematical expressions (those that appear within a line of text), you should enclose the expression in a single dollar sign on each side. For example:
   - The formula for the area of a circle with radius $r$ is given by $A = \pi r^2$.
2. For displayed mathematical expressions (those that are centered and on their own line), you should enclose the expression in double dollar signs or use the LaTeX display math environment and square brackets. For example:
- The quadratic formula is given by:
     $$x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}$$
Here's how the provided examples should be formatted:
- The central equation is the Einstein Field Equation:
  $$G_{\mu\nu} + \Lambda g_{\mu\nu} = \frac{8\pi G}{c^4} T_{\mu\nu}$$
  Where:
  - $G_{\mu\nu}$ is the Einstein tensor, representing the curvature of spacetime. $\Lambda$ is the cosmological constant. 
  """

    prompt= f""" 
        Who you are: [begin] {who_you_are} [end].
        User perefered learning style: [begin] {self.learning_style} [end].
        This is the plan you devised for the course: [begin] {self.plan} [end].
        this is a hint about what you should do now: [begin] {next_step} [end]
        this is the topics that has been covered of the plan [last_covered]: {covered_topics}. (if 0 means nothing from plan has been covered so far)
        This is the last 10 messages of the conversation between you (you are the system) and the user: [begin] {last_10_messages} [end].


        You already send a lot of message to the user based on the plan. You dont have access to all the messages between you and the user. 
        So the hint is a good clue for you to understand at which part the plan you are at right now.

        Now continue the conversation based on the follwoing instruction:
        1- refer to the last 10 messages of the conversation, the hint about you should do now, and the plan: 
            1-1- if you are to start a topic, directly mention which topic of the plan you are explaining (and bring its number like this 1.3 - <topic from plan> ), 
            you explain that topic very extesively and covers all the angles for the user. If the topic is too big and you need to break it down to sub topics and explain each one do that.
            1-2- if You answer the user question, Questions are good clues of user knowledge gaps, so you drill down and persist untill you cover the gap compeltely.
        2- for the tone and theme of your answer, refer to Who you are, User perefered learning style
        3- You are the system. So you continue disscusion as the system. You are the system so should never answer like this 'user = ...' . 
        4- avoid repeating yourself, you continue the conversation as user want, dont loop around or repeat yourself.
        5- 
      """
    prompt = prompt + math_prompt
    
    max_retries = len(self.api_keys)+2
    retries = 0
    while retries <= max_retries:
        try:
            # Randomly select an API key for each call
            openai.api_key = self.api_keys[retries % len(self.api_keys)]
            parsed_response = openai.ChatCompletion.create(
                model = self.conversation_model,
                messages=[
                    {"role": "system", "content":prompt},
                    {"role": "user", "content":user_input},
                ],
                temperature=self.temperature,
                max_tokens=self.chat_max_tokens,
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


    



    

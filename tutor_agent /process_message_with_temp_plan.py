
from config import Topics_table, message_table, user_table
from mytiktoken import count_tokens
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


def process_message_with_temp_plan_method(self, user_input):
    
    self.state = 1  
    
    self.create_message_in_db_and_update_state(f"user: {user_input}")
    
    self.messages_queue.append(f"user: {user_input}")
    
    # Consume the response from the chat method
    full_response = []


    context = ''.join(self.messages_queue)
    background_thread = threading.Thread(target=self.extract_plan_learning_style, args=(context,))
    background_thread.start()

    
    for chunk in self.process_with_temp_plan(user_input):
        yield chunk
        full_response.append(chunk)


    # Set self.system_content and execute the rest of the code once the full response has been received
    self.system_content = f"{''.join(full_response)}"
    if not self.system_content.startswith('system:'):
        self.system_content = f'system: {self.system_content}'


    self.create_message_in_db_and_update_state(self.system_content)
    self.messages_queue.append(self.system_content)

    return

def process_with_temp_plan_method(self, user_input):

    who_you_are = self.topic['who_you_are']
    messages = concatenate_with_spaces(self.messages_queue)

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
        You are the system.
        System Conversation Guidelines :

    - Your Role and Identity: [begin] {who_you_are} [end].
    - Conversation History: [begin] {messages} [end].

    Tasks: 
    1. Extract user's preferred teaching style and learning plan from the conversation history.
    2. Continue the conversation with the following instructions:

            a. Topic Initiation:
            - If new to the plan, start with the first topic.
            - If continuing, resume from the last covered topic.

            b. Topic Identification:
            - Before explaining, state the topic's number and name (e.g., "1.1 - Topic Name").

            c. Explanation Method:
            - Thoroughly explain the topic.
            - Break down into subtopics if complex.

            d. Addressing Knowledge Gaps:
            - Use user questions to spot and fill gaps in understanding."


    3. Adapt the tone and theme of your responses based on your role and the user's learning preferences.
    4. Maintain the perspective of the system throughout the conversation.
    5. Ensure the conversation progresses without repetition or redundancy.
    6.
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


    



    

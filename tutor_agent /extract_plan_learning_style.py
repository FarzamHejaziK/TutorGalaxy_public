from config import Topics_table
import re
import time 
import random
import openai




def extract_plan_learning_style_method(self,context):
    print('Background process started.')
    max_retries = len(self.api_keys)+2
    retries = 0
    prompt= f"""this is the record of a conversation between a user and a system:[begin] {context} [end].
in this conversation, the system put out some options for the learning style and the user expressed a preference for learning style,
extract the learning style that user chose, this include the explaiantion of that style from systems options. If user chose a mix of some otions extract a comperehensive explaination that explain what that mix means. 
Morever the system devised a plan for learning journey of the user, extract that as well, like copy and paste with all the details.
Then give me the extracted info in this format and nothing else:
    "learning_style":"<your extracted learning style and the explaination fot it>",
    "plan":"<your extracted plan>"
      """
    while retries <= max_retries:
        try:
            # Randomly select an API key for each call
            openai.api_key = self.api_keys[retries % len(self.api_keys)]
            parsed_response = openai.ChatCompletion.create(
                model = self.extraction_model,
                messages=[
                    {"role": "system", "content":prompt.format(context)},
                ],
                temperature = 0,
                max_tokens = self.chat_max_tokens
            )
            content = parsed_response["choices"][0]["message"]["content"]
            self.analyse_content(content)
            print('Background process finished.')
            return
        except Exception as e:
            print(f"Error in chat method: {e}")
            retries += 1
            if retries <= max_retries:
                print("Retrying with a new API key...")
                time.sleep(1)
            else:
                return "Sorry, there was an issue connecting to the API. Please try again later."
    

def analyse_content_method(self,content):
    keys = ['learning_style', 'plan']
    parsed_values = {}
    #print("input", post_sequence_string)
    for key in keys:
        # Construct the regex pattern to match 'Key'="Value",
        pattern = r'"' + key + r'"\s*:\s*"([^"]*)'
        match = re.search(pattern, content)
        if match:
            parsed_values[key] = match.group(1).strip()
    
    learning_style = parsed_values.get("learning_style")
    plan = parsed_values.get("plan")
    Topics_table.update_item(
        Key={
            'userId': self.user_email,
            'topics_id': self.topic_id,
        },
        UpdateExpression="SET #p = :i, learning_style = :j",
        ExpressionAttributeValues={
            ':i': plan,
            ':j': learning_style,
        },
        ExpressionAttributeNames={
            "#p": "plan",
        },
        ReturnValues="UPDATED_NEW"
    )



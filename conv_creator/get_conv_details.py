import re

def get_conv_details_method(self, post_sequence_string):
    keys = ['topic', 'goal', 'chatstarter', 'chat','langid','lang_name','monaco_name','learning',
    'creativity','GQA','nickname','secrets_revealed','user_pref','category',
    'learning_persona','creative_persona','learning_style','persona_pref','tutor_bahaviour']
    parsed_values = {}
    #print("input", post_sequence_string)
    for key in keys:
        # Construct the regex pattern to match 'Key'="Value",
        pattern = r'"' + key + r'"\s*:\s*"([^"]*)'
        match = re.search(pattern, post_sequence_string)
        if match:
            parsed_values[key] = match.group(1).strip()
    
    topic = parsed_values.get("topic")
    goal = parsed_values.get("goal")
    langid = parsed_values.get("langid")
    langname = parsed_values.get("lang_name")
    monaconame = parsed_values.get("monaco_name")
    learning = parsed_values.get("learning")
    creativity = parsed_values.get("creativity")
    GQA = parsed_values.get("GQA")
    nickname = parsed_values.get("nickname")
    if  not nickname or nickname == '-1': nickname = ''
    secrets_revealed = parsed_values.get("secrets_revealed")
    user_pref = parsed_values.get("user_pref")
    category = parsed_values.get("category","2")
    if category not in ['1','2','3','4']: category = '4'
    learning_persona = parsed_values.get("learning_persona") 
    if learning_persona == '-1': learning_persona = ''
    creative_persona = parsed_values.get("creative_persona")
    if creative_persona == '-1': creative_persona = ''
    learning_style = parsed_values.get("learning_style")
    if learning_style == '-1': learning_style = ''
    persona_pref = parsed_values.get("persona_pref")
    tutor_bahaviour = parsed_values.get("tutor_bahaviour", 1) 

    self.topic_details = {
        'goal' : goal,
        'topic' : topic,
        'langid' : langid,
        'lang_name' : langname,
        'monaco_name': monaconame,
        'learning': learning,
        'creativity': creativity,
        'GQA' : GQA,
        'user_pref': user_pref,
        'category': category,
        'nickname': nickname,
        'secrets_revealed': secrets_revealed,
        'learning_persona': learning_persona,
        'creative_persona': creative_persona,
        'learning_style': learning_style,
        'persona_pref': persona_pref, 
        'tutor_bahaviour': tutor_bahaviour
    }


    return
import tiktoken
encoding = tiktoken.encoding_for_model("gpt-4")
def count_tokens(s):
    return len(encoding.encode(s)) 


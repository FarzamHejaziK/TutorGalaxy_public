
from config import Topics_table, message_table, user_table
from mytiktoken import count_tokens
import threading
from math import floor

def concatenate_with_spaces(arr):
    result = ""
    for string in arr:
        result += string + " "
    result = result.rstrip()  # Remove trailing space
    return result

def process_message_method(self, user_input):
        
        if self.state == 0:
            prompt = f""
        
            # Consume the response from the chatstarter method
            full_response = []
            for chunk in self.chatstarter(prompt):
                yield chunk
                full_response.append(chunk)

            
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

            #self.tempplan = False
            for buffered_chunk in self.chat(prompt):
                yield buffered_chunk
                full_response.append(buffered_chunk)
            
            #if self.tempplan:
            #    context = ''.join(self.discussion + ''.join(full_response))
            #    background_thread = threading.Thread(target=self.extract_plan_learning_style, args=(context,))
            #    background_thread.start()


            

            # Set self.system_content and execute the rest of the code once the full response has been received
            self.system_content = f"{''.join(full_response)}"
            self.create_message_in_db_and_update_state(self.system_content)
            self.messages_queue.append(self.system_content)
            prompt = f"summary so far:{self.summary}, {concatenate_with_spaces(self.messages_queue)}"
            print('token counts:',count_tokens(prompt) + self.chat_continue_prompt_token_number)
            try:
                if count_tokens(prompt) + self.chat_continue_prompt_token_number >= self.max_token_allowed:
                    self.len_purge_queue = floor(len(self.messages_queue)/2)
                    self.purge_queue = self.messages_queue[:self.len_purge_queue]
                    self.messages_queue = self.messages_queue[self.len_purge_queue:]
                    prompt = f"summary so far:{self.summary}, {concatenate_with_spaces(self.purge_queue)}"
                    yield "[REST]"
                    self.summary = self.summarizer(prompt)
                    yield "[REST]"
                    self.update_summary_and_messages_queue()     
            except Exception as e:
                print(f"An error occurred: {e}")     
            return

def process_with_buffer_method(self, prompt):

    ongoing_string = ""
    iteration_counter = 0
    seen_bracket = False  # Variable to track if '[' has been seen
    chunk_count_after_bracket = 0  # Counter for chunks after seeing '['

    for chunk in self.chat(prompt):
        #print(chunk, end="")
        iteration_counter += 1

        if iteration_counter <= 4:
            ongoing_string += chunk 
            if "system:" in ongoing_string:
                ongoing_string = ongoing_string.replace("system:", "")
            continue
        
        if iteration_counter == 5:
            ongoing_string += chunk
            yield ongoing_string
            ongoing_string = ""
            continue 

        
        if '[' in chunk:
            seen_bracket = True  # Set flag when '[' is seen
            ongoing_string += chunk  # Start accumulating chunks in ongoing_string
        elif seen_bracket:
            chunk_count_after_bracket += 1  # Increment counter after '[' has been seen
            ongoing_string += chunk  # Continue accumulating chunks in ongoing_string
            
            # Check for [PLAN] or [EX] within 3 chunks after seeing '['
            if chunk_count_after_bracket <= 3:
                if "[PLAN]" in ongoing_string:
                    self.plan_done = True
                    self.tempplan = True
                    #print("***************** I am here ************************")
                    ongoing_string = ongoing_string.replace("[PLAN]", "")
                elif "[EX]" in ongoing_string:
                    self.execution_done = True
                    ongoing_string = ongoing_string.replace("[EX]", "")
                else:
                    continue  # Wait for next chunk if [PLAN] or [EX] is not found yet
            else:
                # Clear ongoing_string and buffer if [PLAN] or [EX] is not found within 3 chunks
                seen_bracket = False  # Reset flag
                chunk_count_after_bracket = 0  # Reset counter
        
        # If buffer and ongoing_string are cleared, and '[' is not seen in chunk, yield the chunk
        if not seen_bracket:
            yield chunk
        
        # If '[' is detected in the current chunk, process the buffer logic
        if ongoing_string and not seen_bracket:
            yield ongoing_string
            ongoing_string = ""

    # Yield any remaining chunks in the buffer after processing all chunks
    if ongoing_string:
        yield ongoing_string
        ongoing_string = ""
    



    

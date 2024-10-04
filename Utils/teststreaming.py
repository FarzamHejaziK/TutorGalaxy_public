import requests
import json
import time

headers = {
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTY4ODA2MTMwMywianRpIjoiOWYyZjNmYjUtM2U2NC00NzlmLTllYjQtNGQ5OWI2ZTQxYmUyIiwidHlwZSI6ImFjY2VzcyIsInN1YiI6ImZhcnphbS5oZWphemlAZ21haWwuY29tIiwibmJmIjoxNjg4MDYxMzAzLCJleHAiOjE2OTA2NTMzMDN9.qJfJ7NJG2ZNTvVmuZa04FGeSnQlAusTnMgJ2S9Sv79k",
    "Content-Type": "application/json"
}
data = {"user_input": "go ahead and continue", "topic": "C++"}

response = requests.post(
    'http://ec2-18-223-182-236.us-east-2.compute.amazonaws.com/api/v1/get_response', 
    headers=headers, 
    json=data,  # use json=data instead of data=json.dumps(data)
    stream=True
)


with open("output.txt", "w") as file:
    for line in response.iter_lines():
        if line:
            decoded_line = line.decode('utf-8')
            file.write(decoded_line + "\n")
            file.flush()  # Flush the file buffer to ensure immediate write

            # Process the message as desired
            print(decoded_line)

        # Check the file for new messages every 1 second
        time.sleep(1)

print("Streaming complete. Check 'output.txt' for the streamed messages.")

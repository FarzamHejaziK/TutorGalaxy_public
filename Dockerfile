# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container to /app
WORKDIR /app

# Add the current directory contents into the container at /app
ADD . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 80 available to the world outside this container
EXPOSE 80

# Run gunicorn with 5 workers when the container launchesCMD ["gunicorn", "-w", "5", "-b", "0.0.0.0:80", "JasonEPwithUser:app"]
CMD ["gunicorn", "-w", "5", "--timeout", "300", "-b", "0.0.0.0:80", "New_for_test_JasonEPwithUser:app"]


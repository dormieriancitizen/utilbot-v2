# Use an official Python runtime as the base image
FROM python:3-alpine
RUN apk add --no-cache git

# Set the working directory in the container
WORKDIR /app

# Copy your project files into the container
COPY requirements.txt ./

# Install any project-specific dependencies
RUN pip install -r requirements.txt

# Bundle app source
COPY . .

# Specify the command to run your project
CMD [ "python3", "main.py"]

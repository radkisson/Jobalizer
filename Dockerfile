# Use the official Python image from the Docker Hub
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Install system dependencies and clean up afterward
RUN apt-get update && \
    apt-get install -y sqlite3 build-essential && \
    rm -rf /var/lib/apt/lists/* 

# Set the working directory
WORKDIR /app

# Copy the application code into the container
COPY ./app /app 

# Argument to conditionally generate requirements.txt
ARG GENERATE_REQUIREMENTS="true"

# Conditionally generate requirements.txt
RUN pip install --upgrade pip 

# Copy requirements.txt from the context into the image
COPY ./requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install -r /app/requirements.txt

# Define the command to run the Flask application
CMD ["python", "main.py"]
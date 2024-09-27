# Use the official Python image from the Docker Hub
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Create and set sources.list file for package mirrors
RUN echo "deb http://deb.debian.org/debian bookworm main" > /etc/apt/sources.list && \
    echo "deb http://security.debian.org/debian-security bookworm-security main" >> /etc/apt/sources.list && \
    echo "deb http://deb.debian.org/debian bookworm-updates main" >> /etc/apt/sources.list && \
    apt-get update && \
    apt-get install -y sqlite3 build-essential && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy requirements.txt before copying the rest of the application code
COPY ./requirements.txt /app/requirements.txt

# Upgrade pip and install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r /app/requirements.txt

# Copy the rest of the application code
COPY ./app /app

# Create a non-root user and switch to it for better security
RUN useradd -m jobalizeruser
USER jobalizeruser

# Define the command to run the Flask application
CMD ["python", "main.py"]

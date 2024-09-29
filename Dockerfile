# Stage 1: requirements-builder
FROM python:3.11-slim AS requirements-builder

ENV PYTHONUNBUFFERED=1

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        libpq-dev \
        && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Create and activate a virtual environment, then upgrade pip
RUN python -m venv /venv && \
    /venv/bin/pip install --upgrade pip

# Copy requirements.txt and install Python packages
COPY requirements.txt .
RUN /venv/bin/pip install --no-cache-dir -U -r requirements.txt && \
    /venv/bin/pip freeze > /app/requirements.txt

# Verify that requirements.txt was created successfully
RUN [ -s /app/requirements.txt ] && echo "requirements.txt generated successfully" || { echo "Error: requirements.txt is empty or was not created!"; exit 1; }

# Stage 2: final application image
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

# Install runtime dependencies only (exclude build-essential)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libpq-dev \
        && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Create a non-root user before setting ownership
RUN useradd -m jobalizeruser

# Create and activate a virtual environment, then upgrade pip
RUN python -m venv /venv && \
    /venv/bin/pip install --upgrade pip

# Add /venv/bin to PATH
ENV PATH="/venv/bin:$PATH"

# Copy requirements.txt from the builder stage
COPY --from=requirements-builder /app/requirements.txt /app/requirements.txt

# Install dependencies from requirements.txt
RUN if [ -s /app/requirements.txt ]; then \
        echo "Installing dependencies from requirements.txt without cache..." && \
        pip install --no-cache-dir -r /app/requirements.txt && \
        echo "Installed dependencies:" && \
        pip list; \
    else \
        echo "No requirements.txt found or it is empty. Skipping dependency installation."; \
    fi

# Copy the application code with correct ownership
COPY --chown=jobalizeruser:jobalizeruser . /app/

# Ensure the entrypoint script is owned by the user and executable
COPY --chown=jobalizeruser:jobalizeruser entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose the port the app runs on
EXPOSE 5000

# Switch to the non-root user
USER jobalizeruser

# Set the entrypoint
ENTRYPOINT ["/entrypoint.sh"]

# Define the command to run the Flask application using Gunicorn with eventlet
CMD ["/venv/bin/gunicorn", \
     "-w", "1", \
     "--worker-class", "eventlet", \
     "--bind", "0.0.0.0:5000", \
     "--log-level", "debug", \
     "app:create_app()", \
     "--reload"]

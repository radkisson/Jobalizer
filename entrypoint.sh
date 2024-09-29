#!/bin/bash
set -e

# Activate virtual environment
source /venv/bin/activate

# Set FLASK_APP environment variable
export FLASK_APP=app:create_app
export FLASK_RUN_FROM_CLI=true

# Check for the SQLite database file and create if necessary
if [ ! -f "/app/database.db" ]; then
    echo "Creating SQLite database file..."
    touch /app/database.db
    chmod 664 /app/database.db
fi

# Function to check if migrations are initialized
init_migrations() {
    if [ ! -d "/app/migrations" ] || [ ! -f "/app/migrations/env.py" ]; then
        echo "Initializing Alembic migrations..."
        flask db init
        flask db migrate -m "Initial migration"
    else
        echo "Alembic migrations already initialized."
    fi
}

# Initialize migrations if necessary
init_migrations

# Run database migrations
echo "Applying database migrations..."
flask db upgrade

# Execute the main container command (e.g., Gunicorn)
exec "$@"

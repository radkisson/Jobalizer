# app/__init__.py

import logging
from flask import Flask
from flask_migrate import Migrate
from .models.db import db  # Import db from its module
from .socketio import socketio  # Import socketio from its module
from .config import get_config
from .routes.main_routes import main_bp
from .services.task_queue import init_celery, celery  # Import the initialized Celery app
from .utils.logger import setup_logging

# Initialize Flask-Migrate
migrate = Migrate()

def create_app():
    """
    Application factory function to create and configure the Flask app.
    """
    app = Flask(__name__, template_folder='templates', static_folder='static')

    try:
        # Dynamically load the appropriate config class
        config_class = get_config()
        app.config.from_object(config_class)

        # Set up logging
        setup_logging(app)

        # Log the current configuration for debugging purposes
        app.logger.debug(f"CELERY_BROKER_URL: {app.config.get('CELERY_BROKER_URL')}")
        app.logger.debug(f"CELERY_RESULT_BACKEND: {app.config.get('CELERY_RESULT_BACKEND')}")
        app.logger.debug(f"SOCKETIO_MESSAGE_QUEUE: {app.config.get('SOCKETIO_MESSAGE_QUEUE')}")

        # Initialize extensions
        db.init_app(app)
        migrate.init_app(app, db)
        socketio.init_app(
            app,
            message_queue=app.config['SOCKETIO_MESSAGE_QUEUE'],
            async_mode='eventlet'  # Ensure async_mode is set for Flask-SocketIO
        )

        # Register Blueprints
        app.register_blueprint(main_bp)

        # Initialize Celery with Flask app context
        init_celery(celery_app=celery, flask_app=app)  # Pass the initialized celery app

        # Import models to ensure they are registered with SQLAlchemy
        from .models import database  # Adjust the import path if necessary

        # Log successful initialization
        app.logger.info("Flask application initialized successfully.")

    except Exception as e:
        # Log the exception with stack trace
        app.logger.exception("An error occurred during the Flask app initialization.")
        # Re-raise the exception to prevent the app from starting in an unstable state
        raise e

    return app

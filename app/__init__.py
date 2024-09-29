# app/__init__.py

import logging
from flask import Flask
from flask_migrate import Migrate
from celery import Celery  # Import Celery here
from .models.db import db
from .socketio import socketio
from .config import get_config
from .routes.main_routes import main_bp
from .utils.logger import setup_logging

# Initialize Flask-Migrate
migrate = Migrate()
celery = Celery(__name__)  # Initialize Celery

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
            async_mode='eventlet'
        )

        # Register Blueprints
        app.register_blueprint(main_bp)

        # Initialize Celery with Flask app context
        init_celery(app)

        # Import models to ensure they are registered with SQLAlchemy
        from .models import database

        # Log successful initialization
        app.logger.info("Flask application initialized successfully.")

    except Exception as e:
        # Log the exception with stack trace
        app.logger.exception("An error occurred during the Flask app initialization.")
        # Re-raise the exception to prevent the app from starting in an unstable state
        raise e

    return app

def init_celery(app=None):
    """
    Initializes the Celery app with the Flask app context.
    """
    app = app or create_app()
    celery.conf.update(app.config)
    celery.conf.broker_connection_retry_on_startup = True

    # Define the Celery Task Base Class
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask

    # Import tasks here to register them with Celery
    from .services import task_queue  # Import tasks after Celery is configured

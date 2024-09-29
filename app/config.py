import os
from pathlib import Path

class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass

class Config:
    """Base configuration class with default settings."""

    # Base directory of the project
    BASE_DIR = Path(__file__).resolve().parent.parent

    # Enforce mandatory environment variables
    required_vars = [
        "FLASK_SECRET_KEY",
        "OPENAI_API_KEY"
    ]

    # Validate required environment variables
    @staticmethod
    def validate_env_vars():
        missing_vars = [var for var in Config.required_vars if not os.environ.get(var)]
        if missing_vars:
            raise ConfigError(f"Missing required environment variables: {', '.join(missing_vars)}")

    # Initialization and validation of configuration
    def __init__(self):
        self.validate_env_vars()

    # Application secret key for session management
    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY")

    # SQLAlchemy database URI configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get("SQLALCHEMY_DATABASE_URI", "sqlite:///" + str(Path(BASE_DIR) / "app" / "database.db"))

    # Flask environment: 'development', 'testing', 'production'
    FLASK_ENV = os.environ.get("FLASK_ENV", "development")

    # OpenAI API key for LLM functionality
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

    # Optional configurations with default values
    DEBUG = os.environ.get("FLASK_DEBUG", "false").lower() in ["true", "1", "t"]
    GENERATE_REQUIREMENTS = os.environ.get("GENERATE_REQUIREMENTS", "false").lower() in ["true", "1", "t"]

    # Task queue configurations (Celery & Redis)
    # Updated default from localhost to 'redis' service name
    CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://redis:6379/0")
    CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", CELERY_BROKER_URL)

    # SocketIO message queue configuration
    # Updated default from localhost to 'redis' service name
    SOCKETIO_MESSAGE_QUEUE = os.environ.get("SOCKETIO_MESSAGE_QUEUE", "redis://redis:6379/0")

    # Additional configurations can be added here as required

class DevelopmentConfig(Config):
    """Development-specific configurations."""
    DEBUG = True
    TESTING = False

    # Default to SQLite for local development
    SQLALCHEMY_DATABASE_URI = os.environ.get("SQLALCHEMY_DATABASE_URI", f"sqlite:///{Config.BASE_DIR / 'dev_database.db'}")

class TestingConfig(Config):
    """Testing-specific configurations."""
    DEBUG = True
    TESTING = True

    # Use an in-memory database for testing
    SQLALCHEMY_DATABASE_URI = os.environ.get("SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:")

class ProductionConfig(Config):
    """Production-specific configurations."""
    DEBUG = False
    TESTING = False

    # Use the database URI from environment variables for production
    SQLALCHEMY_DATABASE_URI = os.environ.get("SQLALCHEMY_DATABASE_URI")

    # Access SECRET_KEY correctly and perform the check
    SECRET_KEY = Config.SECRET_KEY

    # Recommended to raise an error if secret keys are set to defaults
    if SECRET_KEY == "your_default_secret_key" or not SECRET_KEY:
        raise ConfigError("FLASK_SECRET_KEY must be set in a production environment and should not be 'your_default_secret_key'.")

# Utility function to get the appropriate configuration class
def get_config():
    env = os.environ.get("FLASK_ENV", "development").lower()
    if env == "production":
        return ProductionConfig()
    elif env == "testing":
        return TestingConfig()
    else:
        return DevelopmentConfig()

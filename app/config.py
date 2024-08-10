import os

class Config:
    # Other configurations...
    DATABASE = os.path.join(os.getcwd(), 'database.db')

# Ensure the app uses this configuration
# app.py or main.py

from flask import Flask
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# Other app setup code...
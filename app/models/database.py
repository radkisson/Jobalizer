# app/models/database.py

from .db import db
import sqlite3
import os

# Database model remains as previously defined
class JobPosting(db.Model):
    __tablename__ = 'job_postings'
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), nullable=False, default='new')
    fields = db.Column(db.Text)  # JSON data as string

    def __init__(self, content, status='new', fields=None):
        self.content = content
        self.status = status
        self.fields = fields

    def __repr__(self):
        return f"<JobPosting(id={self.id}, status={self.status})>"

    def to_dict(self):
        """
        Convert the model instance to a dictionary for easier serialization.
        """
        return {
            "id": self.id,
            "content": self.content,
            "status": self.status,
            "fields": self.fields
        }

# Define the database connection function if needed
def get_db_connection():
    db_path = os.environ.get("DATABASE_URL", "sqlite:///database.db")
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection

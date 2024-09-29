# app/services/task_queue.py

from celery import Celery
from celery.schedules import crontab
import json
import logging
from app.services.openai_service import extract_fields_with_openai
from app.models.database import JobPosting
from app.models.db import db
from app.socketio import socketio
import os

# Initialize the Celery app with Flask's configuration
def make_celery(flask_app):
    """
    Creates a new Celery object and configures it with the Flask app's settings.
    
    Args:
        flask_app (Flask): The Flask application instance.
    
    Returns:
        Celery: Configured Celery instance.
    """
    celery_app = Celery(
        flask_app.import_name,
        broker=flask_app.config['CELERY_BROKER_URL'],
        backend=flask_app.config['CELERY_RESULT_BACKEND']
    )
    
    # Update Celery configuration with Flask app's config
    celery_app.conf.update(flask_app.config)
    
    # Address Celery deprecation warnings
    celery_app.conf.broker_connection_retry_on_startup = True  # Retain existing retry behavior
    
    # Optional: Configure Celery beat schedules if needed
    # celery_app.conf.beat_schedule = {
    #     'some-task-name': {
    #         'task': 'app.services.task_queue.some_task',
    #         'schedule': crontab(minute='*/5'),  # Every 5 minutes
    #         'args': ()
    #     },
    # }
    
    class ContextTask(celery_app.Task):
        """
        Celery Task that ensures each task runs within the Flask app context.
        """
        def __call__(self, *args, **kwargs):
            with flask_app.app_context():
                return self.run(*args, **kwargs)
    
    celery_app.Task = ContextTask
    return celery_app

# Initialize Celery without an app context
celery = Celery(__name__)

def init_celery(celery_app=None, flask_app=None):
    """
    Initializes the Celery application using the given Flask app's context.
    
    Args:
        celery_app (Celery, optional): An existing Celery app instance.
        flask_app (Flask, optional): The Flask application instance.
    
    Returns:
        Celery: Configured Celery instance.
    """
    if flask_app:
        celery_app = make_celery(flask_app)
    else:
        # If no Flask app is provided, ensure Celery is initialized with defaults
        celery_app = celery
        celery_app.conf.update(
            broker_url=os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/0'),
            result_backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://redis:6379/0'),
            broker_connection_retry_on_startup=True  # Retain existing retry behavior
        )
    
    return celery_app

@celery.task(bind=True, max_retries=3, default_retry_delay=60)
def process_job_posting(self, job_posting_id):
    """
    Process the job posting with the given ID.
    Extracts fields using OpenAI and updates the database.
    
    Args:
        self (Task): The Celery task instance.
        job_posting_id (int): The ID of the job posting to process.
    """
    logger = logging.getLogger(__name__)
    
    try:
        # Retrieve the job posting from the database
        job_posting = JobPosting.query.get(job_posting_id)
        if not job_posting:
            logger.error(f"Job posting with ID {job_posting_id} not found.")
            return
        
        logger.debug(f"Processing JobPosting ID: {job_posting_id}")
        
        # Use OpenAI service to extract fields
        fields = extract_fields_with_openai(job_posting.content)
        logger.debug(f"Extracted fields for JobPosting ID {job_posting_id}: {fields}")
    
        # Update the database with extracted fields
        job_posting.status = 'processed'
        job_posting.fields = json.dumps(fields)
        db.session.commit()
        logger.info(f"JobPosting ID {job_posting_id} marked as processed.")
    
        # Emit a SocketIO event with the extracted fields
        socketio.emit('job_processed', {'id': job_posting_id, 'fields': fields})
        logger.debug(f"SocketIO event 'job_processed' emitted for JobPosting ID {job_posting_id}.")
    
    except Exception as e:
        logger.exception(f"Error processing job posting {job_posting_id}: {e}")
        try:
            # Optionally, update the job posting status to 'failed'
            job_posting = JobPosting.query.get(job_posting_id)
            if job_posting:
                job_posting.status = 'failed'
                db.session.commit()
                logger.info(f"JobPosting ID {job_posting_id} marked as failed.")
        except Exception as inner_e:
            logger.exception(f"Error updating JobPosting ID {job_posting_id} to failed: {inner_e}")
        
        # Retry the task
        self.retry(exc=e)

def add_to_queue(job_posting_content):
    """
    Adds a job posting to the processing queue using Celery.
    
    Args:
        job_posting_content (str): The content of the job posting to process.
    """
    logger = logging.getLogger(__name__)
    
    try:
        # Insert the job posting and get its ID
        new_job_posting = JobPosting(content=job_posting_content, status='new')
        db.session.add(new_job_posting)
        db.session.commit()
        logger.info(f"New JobPosting created with ID {new_job_posting.id}.")
    
        # Enqueue the task with the new job posting ID
        process_job_posting.delay(new_job_posting.id)
        logger.info(f"JobPosting ID {new_job_posting.id} added to Celery queue.")
    except Exception as e:
        logger.exception(f"Error adding job posting to queue: {e}")
        # Optionally, handle the failure to enqueue the task (e.g., notify administrators)

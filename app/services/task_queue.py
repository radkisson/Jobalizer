# app/services/task_queue.py

import json
import logging
from app.services.openai_service import extract_fields_with_openai
from app.models.database import JobPosting
from app.models.db import db
from app.socketio import socketio
from app import celery  # Import Celery instance from app

@celery.task(bind=True, max_retries=3, default_retry_delay=60)
def process_job_posting(self, job_posting_id):
    """
    Process the job posting with the given ID.
    Extracts fields using OpenAI and updates the database.
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
        self.retry(exc=e)

def add_to_queue(job_posting_id):
    """
    Adds a job posting to the processing queue using Celery.
    """
    logger = logging.getLogger(__name__)

    try:
        # Enqueue the task with the job posting ID
        process_job_posting.delay(job_posting_id)
        logger.info(f"JobPosting ID {job_posting_id} added to Celery queue.")
    except Exception as e:
        logger.exception(f"Error adding job posting to queue: {e}")

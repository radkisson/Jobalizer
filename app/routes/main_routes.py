from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from ..models.db import db  # Import db from db.py
from ..models.database import JobPosting  # Import the JobPosting model
from ..services.openai_service import extract_fields_with_openai
from ..services.task_queue import add_to_queue

import logging

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    try:
        # Use SQLAlchemy to fetch all job postings
        job_postings = JobPosting.query.all()
    except Exception as e:
        logging.error(f"Error fetching job postings: {e}")
        flash('An error occurred while fetching job postings.')
        job_postings = []
        
    return render_template('index.html', job_postings=job_postings)

@main_bp.route('/input', methods=['POST'])
def input_job_posting():
    job_posting_content = request.form['job_posting']
    
    try:
        # Create a new JobPosting object and add it to the session
        new_job_posting = JobPosting(content=job_posting_content, status='new')
        db.session.add(new_job_posting)
        db.session.commit()
    except Exception as e:
        logging.error(f"Error inserting job posting: {e}")
        flash('An error occurred while adding the job posting.')
        return redirect(url_for('main.index'))

    add_to_queue(new_job_posting.id)  # Pass the job_posting_id instead of content
    flash('Job posting added to queue. Please wait for processing.')
    return redirect(url_for('main.index'))

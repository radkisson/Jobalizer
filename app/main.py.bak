import sqlite3
import threading
import openai
import json
import logging
import os
from flask import Flask, request, redirect, url_for, flash, render_template
from flask_socketio import SocketIO, emit
from config import *
from app.models.database import get_db_connection, init_db, init_app

app = Flask(__name__, template_folder=os.path.join('web', 'templates'))
app.config.from_object(Config)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "your_secret_key") 
socketio = SocketIO(app)

# Initialize database functions
init_app(app)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize database if it doesn't exist
with app.app_context():
    try:
        init_db()
    except sqlite3.OperationalError as e:
        logging.error(f"Database initialization failed: {e}")

# Function to add job posting to queue
def add_to_queue(job_posting):
    """
    Adds a job posting to the processing queue.
    Spawns a new thread to process the job posting.
    """
    def process_job_posting(job_posting):
        """
        Processes the job posting using OpenAI to extract fields.
        Updates the database with the processed status and extracted fields.
        Emits a SocketIO event with the extracted fields.
        """
        try:
            fields = extract_fields_with_openai(job_posting)

            with app.app_context():
                # Update the database with the processed status and extracted fields
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE job_postings SET status = ?, fields = ? WHERE id = ?",
                    ("processed", json.dumps(fields), job_posting["id"])
                )
                conn.commit()
                conn.close()

                # Emit a SocketIO event with the extracted fields
                socketio.emit('job_processed', fields)

        except Exception as e:
            logging.error(f"Error processing job posting: {e}")

    # Spawn a new thread to process the job posting
    threading.Thread(target=process_job_posting, args=(job_posting,)).start()

# Function to extract fields using OpenAI's LLM
def extract_fields_with_openai(job_posting):
    """
    Extracts specific fields from a job posting using OpenAI's language model.

    Args:
        job_posting (str): The job posting text to extract fields from.

    Returns:
        dict: A dictionary containing the extracted fields.
    """

    prompt = f"""Extract the following information from this job posting, 
    return a JSON object with the extracted data:
    ```json
    {{
        "Job Title": "",
        "Company Name": "",
        "Location": "",
        "Salary": "",
        "Job Description": ""
    }}
    ```
    Job Posting:
    {job_posting}
    """

    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=150
    )

    return json.loads(response.choices[0].text.strip())

# Route for inputting job postings
@app.route('/input', methods=['POST'])
def input_job_posting():
    job_posting = request.form['job_posting']
    
    try:
        with app.app_context():
            db = get_db_connection()
            db.execute('INSERT INTO job_postings (content, status) VALUES (?, ?)', 
                       (job_posting, 'new'))
            db.commit()
    except Exception as e:
        logging.error(f"Error inserting job posting: {e}")
        flash('An error occurred while adding the job posting.')
        return redirect(url_for('index'))
    finally:
        db.close()

    add_to_queue(job_posting)
    flash('Job posting added to queue. Please wait for processing.')
    return redirect(url_for('index'))

# Route for displaying the main page
@app.route('/')
def index():
    print("ssdfsdfsdf")
    try:
        with app.app_context():
            db = get_db_connection()
            job_postings = db.execute('SELECT * FROM job_postings').fetchall()
    except Exception as e:
        logging.error(f"Error fetching job postings: {e}")
        flash('An error occurred while fetching job postings.')
        job_postings = []
    finally:
        db.close()
        
    return render_template('index.html', job_postings=job_postings)

if __name__ == '__main__':
    # Ensure the app context is properly set up
    with app.app_context():
        try:
            init_db()
            logging.info("Database initialized successfully.")
        except Exception as e:
            logging.error(f"Database initialization failed: {e}")
            exit(1)  # Exit if the database initialization fails

    # Run the SocketIO server
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)

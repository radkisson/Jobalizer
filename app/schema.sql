-- schema.sql
-- This file defines the database schema for the job postings application.

-- Table: job_postings
-- This table stores job postings received from users and their processing status.

CREATE TABLE job_postings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,  -- Unique identifier for each job posting
    content TEXT NOT NULL,                   -- Job posting content (not null)
    status TEXT NOT NULL,                    -- Status of the job posting (not null)
    fields TEXT                              -- Extracted fields in JSON format (optional)
);

-- Possible statuses for job postings:
-- 'new'      - The job posting has been received and is awaiting processing.
-- 'processing' - The job posting is currently being processed (optional status for tracking).
-- 'processed'  - The job posting has been processed, and fields have been extracted.
-- 'error'     - There was an error during the processing of the job posting.

-- Note: The `fields` column will contain JSON data representing extracted information from the job posting.
-- Example JSON structure for the `fields` column:
-- {
--    "Job Title": "Software Engineer",
--    "Company Name": "Tech Corp",
--    "Location": "New York, NY",
--    "Salary": "$100,000",
--    "Job Description": "Responsible for developing software solutions."
-- }

-- Possible further enhancements could include additional tables:
-- For example, if you want to track users, you can add a users table.
-- CREATE TABLE users (
--     id INTEGER PRIMARY KEY AUTOINCREMENT,
--     username TEXT NOT NULL UNIQUE,
--     password TEXT NOT NULL
-- );
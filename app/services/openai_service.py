import openai
import json
from flask import current_app

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

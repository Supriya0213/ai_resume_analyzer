from google import genai
import os
from dotenv import load_dotenv
import json
import time

# ---------- Load API key from .env ----------
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# List of models to try, in order of preference
MODELS_TO_TRY = ["gemini-3.5-flash-lite", "gemini-2.5-flash"]


def call_gemini_with_fallback(prompt):
    """Try each model in MODELS_TO_TRY in order. Return the first successful response."""
    last_error = None

    for model_name in MODELS_TO_TRY:
        max_retries = 2
        for attempt in range(max_retries):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt
                )
                return response  # success — stop trying anything else
            except Exception as e:
                last_error = e
                if "RESOURCE_EXHAUSTED" in str(e) or "429" in str(e):
                    break  # don't retry quota errors, move to next model instead
                elif attempt < max_retries - 1:
                    time.sleep(2)
                # otherwise fall through and try the next model

    # If we reach here, every model failed
    raise RuntimeError(f"All models failed. Last error: {last_error}")


# ---------- Function: extract structured data using Gemini ----------
def extract_resume_data(raw_text):
    prompt = f"""
Extract the following information from this resume text and return ONLY valid JSON, nothing else:

{{
  "name": "full name of the candidate",
  "skills": ["list", "of", "skills"],
  "experience": [
    {{"job_title": "...", "company": "...", "start_date": "...", "end_date": "..."}}
  ],
  "education": [
    {{"degree": "...", "institution": "...", "year": "..."}}
  ]
}}

Resume text:
{raw_text}
"""

    response = call_gemini_with_fallback(prompt)
    result_text = response.text.strip()

    if result_text.startswith("```"):
        result_text = result_text.strip("`").replace("json", "", 1).strip()

    return json.loads(result_text)


# ---------- Function: match resume to job description ----------
def match_resume_to_jd(structured_data, job_description):
    if not job_description.strip():
        return None

    prompt = f"""
You are comparing a candidate's resume data against a job description.

Candidate's data:
{json.dumps(structured_data)}

Job description:
{job_description}

Return ONLY valid JSON in this exact shape, nothing else:

{{
  "match_score": 0-100 (integer, how well the candidate fits this role),
  "matched_skills": ["skills from the resume that align with the job description"],
  "missing_skills": ["important skills/requirements from the job description that the resume lacks"],
  "feedback": "one short paragraph of specific, actionable feedback for the candidate"
}}
"""

    response = call_gemini_with_fallback(prompt)
    result_text = response.text.strip()

    if result_text.startswith("```"):
        result_text = result_text.strip("`").replace("json", "", 1).strip()

    return json.loads(result_text)


# ---------- Quick test ----------
if __name__ == "__main__":
    sample_text = "John Smith is a software engineer with 3 years at Google, skilled in Python, SQL, and React. He has a BS in Computer Science from MIT, 2021."
    result = extract_resume_data(sample_text)
    print(result)
from google import genai
import os
from dotenv import load_dotenv
import math

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def get_embedding(text):
    """Convert a piece of text into an embedding (a list of numbers representing its meaning)."""
    result = client.models.embed_content(
        model="gemini-embedding-2",
        contents=text
    )
    return result.embeddings[0].values


def cosine_similarity(vec_a, vec_b):
    """Calculate how similar two vectors are, from 0 (unrelated) to 1 (identical meaning)."""
    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    magnitude_a = math.sqrt(sum(a * a for a in vec_a))
    magnitude_b = math.sqrt(sum(b * b for b in vec_b))

    if magnitude_a == 0 or magnitude_b == 0:
        return 0

    return dot_product / (magnitude_a * magnitude_b)


def semantic_match_score(structured_data, job_description):
    """Compare resume skills against a job description using embeddings, not just keywords."""
    resume_text = ", ".join(structured_data.get("skills", []))

    resume_embedding = get_embedding(resume_text)
    jd_embedding = get_embedding(job_description)

    similarity = cosine_similarity(resume_embedding, jd_embedding)

    # Convert 0-1 similarity into a 0-100 percentage score
    score = round(similarity * 100, 1)

    return score

def rank_resumes_against_jd(resumes, job_description):
    """Rank many resumes against one job description using embeddings.
    resumes is a list of (filename, text) pairs."""
    jd_embedding = get_embedding(job_description)  # embed the JD only once
    results = []

    for filename, text in resumes:
        try:
            resume_embedding = get_embedding(text)
            score = round(cosine_similarity(resume_embedding, jd_embedding) * 100, 1)
            results.append({"Candidate File": filename, "Score": score, "Error": ""})
        except Exception as e:
            results.append({"Candidate File": filename, "Score": None, "Error": str(e)})

    # Highest score first; failed ones go to the bottom
    results.sort(key=lambda r: (r["Score"] is None, -(r["Score"] or 0)))
    return results
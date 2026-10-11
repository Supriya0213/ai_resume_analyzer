import streamlit as st
import pdfplumber
import sqlite3
import pandas as pd
from datetime import datetime
from matching_utils import get_embedding, cosine_similarity

st.set_page_config(page_title="Version Tracker", page_icon="📈")
st.title("📈 Resume Version Tracker")
st.write("Upload different versions of your resume against the same job and see whether your edits improve the match.")


# ---------- Database helpers ----------
def init_table():
    connection = sqlite3.connect("resumes.db")
    connection.execute("""
        CREATE TABLE IF NOT EXISTS SCORE_HISTORY (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            JOB_NAME TEXT NOT NULL,
            VERSION_LABEL TEXT NOT NULL,
            SCORE REAL NOT NULL,
            CREATED_AT TEXT NOT NULL
        )
    """)
    connection.commit()
    connection.close()


def save_score(job_name, version_label, score):
    connection = sqlite3.connect("resumes.db")
    connection.execute(
        "INSERT INTO SCORE_HISTORY (JOB_NAME, VERSION_LABEL, SCORE, CREATED_AT) VALUES (?, ?, ?, ?)",
        (job_name, version_label, score, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    connection.commit()
    connection.close()


def load_history(job_name):
    connection = sqlite3.connect("resumes.db")
    cursor = connection.cursor()
    cursor.execute(
        "SELECT VERSION_LABEL, SCORE, CREATED_AT FROM SCORE_HISTORY WHERE JOB_NAME = ? ORDER BY ID",
        (job_name,)
    )
    rows = cursor.fetchall()
    connection.close()
    return rows


# ---------- PDF helper ----------
def extract_text_from_pdf(file):
    full_text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                full_text += page_text + "\n"
    return full_text


init_table()

# ---------- UI ----------
job_name = st.text_input("Job name (used to group your versions)", placeholder="e.g. Backend Engineer at Acme")
job_description = st.text_area("Paste the job description", height=200)
version_label = st.text_input("Label for this resume version", placeholder="e.g. v1, v2 with more projects")
uploaded_file = st.file_uploader("Upload this version (PDF)", type="pdf")

if st.button("Score and save this version"):
    if not job_name.strip() or not job_description.strip() or not version_label.strip() or uploaded_file is None:
        st.warning("Please fill in every field and upload a PDF.")
    else:
        resume_text = extract_text_from_pdf(uploaded_file)
        if not resume_text.strip():
            st.error("Couldn't read any text from this PDF.")
        else:
            try:
                with st.spinner("Scoring..."):
                    resume_embedding = get_embedding(resume_text)
                    jd_embedding = get_embedding(job_description)
                    score = round(cosine_similarity(resume_embedding, jd_embedding) * 100, 1)
                save_score(job_name.strip(), version_label.strip(), score)
                st.success(f"Saved '{version_label}' with a score of {score}%")
            except Exception as e:
                st.error(f"Scoring failed. Try again in a moment. ({e})")

# ---------- History ----------
if job_name.strip():
    history = load_history(job_name.strip())
    if history:
        st.subheader(f"Score history for: {job_name.strip()}")
        df = pd.DataFrame(history, columns=["Version", "Score", "Saved at"])
        df.insert(0, "Attempt", range(1, len(df) + 1))
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.line_chart(df.set_index("Attempt")["Score"])
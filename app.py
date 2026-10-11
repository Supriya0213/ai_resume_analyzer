import streamlit as st
import pdfplumber
import sqlite3
from datetime import datetime
from extract_data import extract_resume_data, match_resume_to_jd
from matching_utils import semantic_match_score
from ats_checker import run_ats_check



# ---------- Page setup ----------
st.set_page_config(page_title="Resume Analyzer", page_icon="📄")
st.title("📄 Resume Analyzer")
st.write("Upload your resume as a PDF to extract, save, and analyze it.")


# ---------- Function: extract text from PDF ----------
def extract_text_from_pdf(file):
    full_text = ""
    try:
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    full_text += page_text + "\n"
    except Exception:
        st.error("This file couldn't be read. It may be corrupted or password-protected. Please try another PDF.")
        return ""

    if not full_text.strip():
        st.error("No readable text found. This may be a scanned image PDF, which this tool can't read yet.")

    return full_text


# ---------- Function: save raw resume to database ----------
def save_resume_to_db(filename, raw_text):
    """Insert the extracted resume text into the RESUMES table. Returns the new resume's ID."""
    connection = sqlite3.connect("resumes.db")
    cursor = connection.cursor()
    upload_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        "INSERT INTO RESUMES (FILENAME, RAW_TEXT, UPLOAD_DATE) VALUES (?, ?, ?)",
        (filename, raw_text, upload_date)
    )

    connection.commit()
    new_resume_id = cursor.lastrowid
    connection.close()

    return new_resume_id


# ---------- Function: save skills to database ----------
def save_skills_to_db(resume_id, skills):
    """Insert each extracted skill into the SKILLS table."""
    connection = sqlite3.connect("resumes.db")
    cursor = connection.cursor()

    for skill in skills:
        cursor.execute(
            "INSERT INTO SKILLS (RESUME_ID, SKILL_NAME) VALUES (?, ?)",
            (resume_id, skill)
        )

    connection.commit()
    connection.close()


# ---------- Function: save experience to database ----------
def save_experience_to_db(resume_id, experience):
    """Insert each extracted experience into the EXPERIENCE table."""
    connection = sqlite3.connect("resumes.db")
    cursor = connection.cursor()

    for exp in experience:
        cursor.execute(
            "INSERT INTO EXPERIENCE (RESUME_ID, JOB_TITLE, COMPANY_NAME, START_DATE, END_DATE) VALUES (?, ?, ?, ?, ?)",
            (resume_id, exp.get("job_title"), exp.get("company"), exp.get("start_date"), exp.get("end_date"))
        )

    connection.commit()
    connection.close()


# ---------- Function: save education to database ----------
def save_education_to_db(resume_id, education_list):
    """Insert each extracted education entry into the EDUCATION table."""
    connection = sqlite3.connect("resumes.db")
    cursor = connection.cursor()

    for edu in education_list:
        cursor.execute(
            "INSERT INTO EDUCATION (RESUME_ID, INSTITUTION, DEGREE, FIELD_OF_STUDY, YEAR) VALUES (?, ?, ?, ?, ?)",
            (resume_id, edu.get("institution"), edu.get("degree"), edu.get("field_of_study"), edu.get("year"))
        )

    connection.commit()
    connection.close()


# ---------- Function: check for duplicate resumes ----------
def resume_already_exists(filename):
    """Check if a resume with this filename is already in the database."""
    connection = sqlite3.connect("resumes.db")
    cursor = connection.cursor()

    cursor.execute("SELECT ID FROM RESUMES WHERE FILENAME = ?", (filename,))
    result = cursor.fetchone()

    connection.close()
    return result is not None


def get_existing_resume_id(filename):
    """Return the ID of an existing resume with this filename, or None if not found."""
    connection = sqlite3.connect("resumes.db")
    cursor = connection.cursor()

    cursor.execute("SELECT ID FROM RESUMES WHERE FILENAME = ?", (filename,))
    result = cursor.fetchone()

    connection.close()
    return result[0] if result else None


# ---------- Main app logic ----------
uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

job_description = st.text_area("Paste the job description here (optional)", height=200)

if uploaded_file is not None:

    # Only re-run extraction if this is a NEW file (not on every rerun)
    if "processed_filename" not in st.session_state or st.session_state.processed_filename != uploaded_file.name:

        with st.spinner("Extracting text..."):
            extracted_text = extract_text_from_pdf(uploaded_file)

        if extracted_text.strip():

            if resume_already_exists(uploaded_file.name):
                st.warning(f"'{uploaded_file.name}' was already uploaded before — reusing existing data instead of re-analyzing.")
                resume_id = get_existing_resume_id(uploaded_file.name)
            else:
                resume_id = save_resume_to_db(uploaded_file.name, extracted_text)

                try:
                    with st.spinner("Analyzing resume with AI..."):
                        structured_data = extract_resume_data(extracted_text)

                    save_skills_to_db(resume_id, structured_data["skills"])
                    save_experience_to_db(resume_id, structured_data["experience"])
                    save_education_to_db(resume_id, structured_data["education"])

                    st.session_state.structured_data = structured_data

                except Exception as e:
                    st.error(f"AI analysis failed — you can try again in a moment. ({e})")

            st.session_state.processed_filename = uploaded_file.name
            st.session_state.extracted_text = extracted_text
            st.session_state.resume_id = resume_id

    # Display cached results (fast — no API calls here)
    if "structured_data" in st.session_state and st.session_state.processed_filename == uploaded_file.name:
        st.subheader("Extracted Text")
        st.text_area("Resume content", st.session_state.extracted_text, height=400)
        st.success(f"Extracted {len(st.session_state.extracted_text.split())} words.")
        st.info("Saved to database!")

        st.subheader("Structured Data")
        st.json(st.session_state.structured_data)

        st.success("Skills, experience, and education saved to database!")
        st.subheader("ATS Compatibility Check")
        ats_result = run_ats_check(st.session_state.extracted_text)
        st.metric("ATS Score", f"{ats_result['ats_score']}/100")

        if ats_result["issues"]:
            for issue in ats_result["issues"]:
                st.warning(issue)
        else:
            st.success("No major ATS compatibility issues detected!")
        if job_description.strip():
            with st.spinner("Matching resume to job description..."):
                match_result = match_resume_to_jd(st.session_state.structured_data, job_description)

            st.subheader("Job Match Results")
            st.metric("Match Score", f"{match_result['match_score']}%")
            st.write("**Matched Skills:**", ", ".join(match_result['matched_skills']))
            st.write("**Missing Skills:**", ", ".join(match_result['missing_skills']))
            st.write("**Feedback:**", match_result['feedback'])

            semantic_score = semantic_match_score(st.session_state.structured_data, job_description)
            st.metric("Semantic Match Score (Embeddings)", f"{semantic_score}%")
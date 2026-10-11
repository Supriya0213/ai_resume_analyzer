import streamlit as st
import pdfplumber
from matching_utils import rank_resumes_against_jd

st.set_page_config(page_title="Recruiter Mode", page_icon="🧑‍💼")
st.title("🧑‍💼 Recruiter Mode")
st.write("Upload multiple resumes and rank them against one job description.")


def extract_text_from_pdf(file):
    full_text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                full_text += page_text + "\n"
    return full_text


job_description = st.text_area("Paste the job description", height=200)
uploaded_files = st.file_uploader(
    "Upload resumes (PDF)", type="pdf", accept_multiple_files=True
)

if st.button("Rank candidates"):
    if not uploaded_files or not job_description.strip():
        st.warning("Please upload at least one resume and paste a job description.")
    else:
        resumes = []
        for f in uploaded_files:
            text = extract_text_from_pdf(f)
            if text.strip():
                resumes.append((f.name, text))
            else:
                st.warning(f"Couldn't read any text from {f.name}, skipping it.")

        with st.spinner("Ranking candidates..."):
            results = rank_resumes_against_jd(resumes, job_description)

        for position, row in enumerate(results, start=1):
            row["Rank"] = position

        st.subheader("Ranking")
        st.dataframe(results, use_container_width=True)

        scored = {r["Candidate File"]: r["Score"] for r in results if r["Score"] is not None}
        if scored:
            st.bar_chart(scored)
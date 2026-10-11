import streamlit as st
import pdfplumber
from extract_data import call_gemini_with_fallback

st.set_page_config(page_title="Cover Letter Generator", page_icon="✉️")
st.title("✉️ Cover Letter Generator")
st.write("Upload your resume and paste a job description to get a tailored cover letter draft.")


def extract_text_from_pdf(file):
    full_text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                full_text += page_text + "\n"
    return full_text


uploaded_file = st.file_uploader("Upload your resume (PDF)", type="pdf")
job_description = st.text_area("Paste the job description", height=200)
company_name = st.text_input("Company name (optional)")
tone = st.selectbox("Tone", ["Professional", "Friendly", "Confident"])

if st.button("Generate cover letter"):
    if uploaded_file is None or not job_description.strip():
        st.warning("Please upload a resume and paste a job description.")
    else:
        resume_text = extract_text_from_pdf(uploaded_file)

        if not resume_text.strip():
            st.error("Couldn't read any text from this PDF.")
        else:
            company_line = f"The company is {company_name}." if company_name.strip() else ""

            prompt = f"""
Write a cover letter for the candidate below, applying to the job described.

Rules:
- Use ONLY facts that appear in the resume. Do not invent employers, numbers, skills, or achievements.
- Highlight the parts of the resume that best match the job description.
- Tone: {tone}.
- Length: 250 to 300 words, in 3 or 4 short paragraphs.
- Start with "Dear Hiring Manager," and end with "Sincerely," followed by the candidate's name from the resume.
- Return only the letter text, nothing else.

{company_line}

Resume:
{resume_text}

Job description:
{job_description}
"""
            try:
                with st.spinner("Writing your cover letter..."):
                    response = call_gemini_with_fallback(prompt)
                st.session_state.cover_letter = response.text.strip()
            except Exception as e:
                st.error(f"Generation failed. Try again in a moment. ({e})")

if "cover_letter" in st.session_state:
    st.subheader("Your cover letter")
    st.text_area("Review and edit before using", st.session_state.cover_letter, height=400)
    st.download_button(
        "Download as .txt",
        st.session_state.cover_letter,
        file_name="cover_letter.txt"
    )
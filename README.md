# 📄 AI Resume Analyzer

A multi-page application that turns raw resume PDFs into structured data and evaluates them against job descriptions, using both LLM reasoning and embeddings. It works for candidates checking their own resume and for recruiters ranking many candidates.

## Features

| Page | What it does |
|---|---|
| **Resume Analyzer** (main) | Extracts text from a PDF, structures it with an LLM (name, skills, experience, education), stores it in a normalized SQLite database, then scores it against a job description two ways: LLM reasoning with feedback, and embeddings-based semantic similarity. Also runs an ATS-compatibility check. |
| **Recruiter Mode** | Upload many resumes at once and rank them against one job description using embeddings (one cheap call per resume). |
| **Version Tracker** | Score different versions of your resume against the same job and chart whether your edits improve the match. |
| **Cover Letter** | Generates a tailored cover letter grounded only in facts from the resume. |

## Tech stack

| Layer | Technology |
|---|---|
| Interface | Streamlit (multipage) |
| PDF parsing | pdfplumber |
| Database | SQLite |
| LLM and embeddings | Google Gemini API (`google-genai`) |
| Data handling | pandas |

## Project structure

```
resume_analyzer/
├── app.py                  # main page: analyze one resume
├── extract_data.py         # LLM extraction, matching, retry + model fallback
├── matching_utils.py       # embeddings, cosine similarity, ranking
├── ats_checker.py          # ATS compatibility checks
├── database.py             # creates the database from schema.sql
├── schema.sql              # database schema
└── pages/
    ├── 1_Recruiter_Mode.py
    ├── 2_Version_Tracker.py
    └── 3_Cover_Letter.py
```

## Database schema

Normalized into related tables linked by `RESUME_ID` foreign keys:

```
RESUMES  (ID, FILENAME, RAW_TEXT, UPLOAD_DATE)
SKILLS   (ID, RESUME_ID -> RESUMES, SKILL_NAME)
EXPERIENCE (ID, RESUME_ID -> RESUMES, JOB_TITLE, COMPANY_NAME, START_DATE, END_DATE, DESCRIPTION)
EDUCATION  (ID, RESUME_ID -> RESUMES, INSTITUTION, DEGREE, FIELD_OF_STUDY, YEAR)
SCORE_HISTORY (ID, JOB_NAME, VERSION_LABEL, SCORE, CREATED_AT)
```

One resume has many skills, experience entries, and education entries (one-to-many).

## Run it locally

1. Clone the repository and create a virtual environment:
   ```
   python -m venv venv
   venv\Scripts\activate        # Windows
   source venv/bin/activate     # Mac/Linux
   ```
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the project root (see `.env.example`):
   ```
   GEMINI_API_KEY=your_api_key_here
   ```
4. Create the database:
   ```
   python database.py
   ```
5. Start the app:
   ```
   streamlit run app.py
   ```

## Design decisions

- **Normalized schema** instead of one flat table, so skills, experience, and education avoid repeating groups (1NF) and can be queried independently.
- **LLM for extraction, database for memory.** The LLM handles messy, inconsistent text; the database makes results persistent and reusable without paying for repeat API calls.
- **Two matching methods on purpose.** LLM matching gives reasoning and feedback but costs one call per comparison. Embeddings are cheap and scale to many resumes but return only a score. Recruiter Mode uses embeddings for this reason.
- **Resilient API layer.** Retries transient 503 errors, does not retry 429 quota errors, and falls back to a second model if the first is unavailable.
- **Defensive parsing.** LLM output is read with `.get()` and stripped of markdown fences before JSON parsing, since model output is not guaranteed to be clean.
- **Grounded cover letters.** The prompt restricts the model to facts present in the resume to avoid invented achievements.

## Known limitations

- Embedding scores cluster in a narrow range, so rankings are more reliable than absolute percentages.
- Re-uploading an already-processed resume reuses stored data but does not redisplay the structured JSON.
- No user accounts: this is a single-user local tool.
- Foreign keys do not yet use `ON DELETE CASCADE`.
- Depends on Gemini free-tier limits and model availability, which change frequently.

## Possible next steps

- Extract only the requirements section of a job description before embedding it
- Add `ON DELETE CASCADE` and enable SQLite foreign key enforcement
- Add user authentication and deploy with a hosted database

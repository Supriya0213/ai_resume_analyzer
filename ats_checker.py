import re


def check_section_headers(resume_text):
    """Check if standard resume section headers are present."""
    text_lower = resume_text.lower()

    required_sections = {
        "experience": ["experience", "work history", "employment"],
        "education": ["education", "academic"],
        "skills": ["skills", "technical skills", "competencies"],
    }

    found = {}
    for section, keywords in required_sections.items():
        found[section] = any(keyword in text_lower for keyword in keywords)

    missing = [section for section, present in found.items() if not present]
    return {"found": found, "missing": missing}


def check_contact_info(resume_text):
    """Check if an email and phone number are detectable as plain text."""
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    phone_pattern = r'(\+?\d{1,3}[\s-]?)?\(?\d{3,5}\)?[\s-]?\d{3,5}[\s-]?\d{3,5}'

    has_email = bool(re.search(email_pattern, resume_text))
    has_phone = bool(re.search(phone_pattern, resume_text))

    return {"has_email": has_email, "has_phone": has_phone}


def check_length(resume_text):
    """Flag resumes that are suspiciously short or long."""
    word_count = len(resume_text.split())

    if word_count < 150:
        status = "too_short"
    elif word_count > 1200:
        status = "too_long"
    else:
        status = "good"

    return {"word_count": word_count, "status": status}


def check_text_quality(resume_text):
    """Detect signs of garbled extraction, often caused by tables/columns/images in the PDF."""
    lines = resume_text.split("\n")
    very_short_lines = [line for line in lines if 0 < len(line.strip()) <= 2]

    # A high ratio of very short, fragment-like lines often indicates a table/column layout
    # that didn't extract cleanly as linear text
    ratio = len(very_short_lines) / len(lines) if lines else 0
    likely_garbled = ratio > 0.15

    return {"likely_garbled": likely_garbled, "fragment_line_ratio": round(ratio, 2)}


def run_ats_check(resume_text):
    """Run all ATS checks and return a combined report with an overall score."""
    sections = check_section_headers(resume_text)
    contact = check_contact_info(resume_text)
    length = check_length(resume_text)
    quality = check_text_quality(resume_text)

    issues = []

    if sections["missing"]:
        issues.append(f"Missing standard section headers: {', '.join(sections['missing'])}")

    if not contact["has_email"]:
        issues.append("No email address detected — ATS systems may fail to extract contact info")

    if not contact["has_phone"]:
        issues.append("No phone number detected")

    if length["status"] == "too_short":
        issues.append(f"Resume seems too short ({length['word_count']} words) — may lack sufficient detail")
    elif length["status"] == "too_long":
        issues.append(f"Resume seems too long ({length['word_count']} words) — consider trimming")

    if quality["likely_garbled"]:
        issues.append("Text extraction looks fragmented — the PDF may use tables/columns that confuse ATS parsers")

    # Simple scoring: start at 100, deduct per issue
    score = max(0, 100 - (len(issues) * 15))

    return {
        "ats_score": score,
        "issues": issues,
        "details": {
            "sections": sections,
            "contact": contact,
            "length": length,
            "quality": quality,
        }
    }
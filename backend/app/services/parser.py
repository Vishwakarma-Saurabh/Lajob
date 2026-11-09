import re
import spacy
import pdfplumber

# Load once at import time — spaCy models are expensive to load per request
nlp = spacy.load("en_core_web_sm")

# A curated skill list.
SKILL_KEYWORDS = [
    "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust",
    "react", "angular", "vue", "node.js", "django", "flask", "fastapi",
    "sql", "postgresql", "mysql", "mongodb", "redis",
    "docker", "kubernetes", "aws", "gcp", "azure", "terraform",
    "machine learning", "deep learning", "nlp", "pytorch", "tensorflow",
    "scikit-learn", "pandas", "numpy", "data analysis", "data science",
    "html", "css", "git", "linux", "rest api", "graphql",
    "celery", "playwright", "selenium", "ci/cd", "agile", "scrum",
]


def extract_text_from_pdf(file_path: str) -> str:
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text.strip()


def parse_resume(file_path: str) -> dict:
    raw_text = extract_text_from_pdf(file_path)
    if not raw_text:
        return {
            "raw_text": "",
            "email": None,
            "phone": None,
            "skills": [],
            "education": [],
            "experience_years": None,
            "error": "No text found in PDF (may be a scanned image).",
        }

    doc = nlp(raw_text.lower())

    email_match = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", raw_text)
    email = email_match.group(0) if email_match else None

    phone_match = re.search(r"(\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}", raw_text)
    phone = phone_match.group(0).strip() if phone_match else None

    text_lower = raw_text.lower()
    found_skills = []
    for skill in SKILL_KEYWORDS:
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, text_lower):
            found_skills.append(skill)

    degree_patterns = [
        r"b\.?tech", r"b\.?e\.?", r"bachelor", r"m\.?tech", r"master",
        r"mba", r"ph\.?d", r"b\.?sc", r"m\.?sc",
    ]
    education = []
    for deg in degree_patterns:
        if re.search(deg, text_lower):
            match = re.search(deg, text_lower)
            start = max(0, match.start() - 20)
            end = min(len(raw_text), match.end() + 60)
            snippet = raw_text[start:end].strip()
            if snippet not in education:
                education.append(snippet)
            break  

    exp_match = re.search(r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)", text_lower)
    experience_years = float(exp_match.group(1)) if exp_match else None

    return {
        "raw_text": raw_text,
        "email": email,
        "phone": phone,
        "skills": sorted(found_skills),
        "education": education,
        "experience_years": experience_years,
        "error": None,
    }
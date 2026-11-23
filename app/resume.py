import re
from pathlib import Path

SKILL_VOCAB = [
"python","java","javascript","typescript","c++","c#","html","css","react","flask","django",
"sql","postgresql","mysql","mongodb","pandas","numpy","scikit-learn","machine learning",
"deep learning","nlp","spacy","tensorflow","pytorch","data analysis","statistics","excel",
"power bi","tableau","data visualization","git","docker","linux","aws","azure","cloud",
"rest api","api","testing","selenium","qa","figma","ui design","ux design","communication",
"problem solving","networking","cybersecurity","etl","data engineering","spring","agile",
"ci/cd","transformers","research","prototyping","mobile development","windows"
]

def extract_text(path, suffix):
    if suffix == ".pdf":
        import pdfplumber
        with pdfplumber.open(path) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages)
    if suffix == ".docx":
        from docx import Document
        return "\n".join(p.text for p in Document(path).paragraphs)
    raise ValueError("Only PDF and DOCX files are supported.")

def extract_skills(text):
    normalized = text.lower()
    found = []
    for skill in SKILL_VOCAB:
        pattern = r"(?<![a-z0-9])" + re.escape(skill) + r"(?![a-z0-9])"
        if re.search(pattern, normalized):
            found.append(skill)
    return sorted(set(found))

def sections(text):
    lines = [x.strip() for x in text.splitlines() if x.strip()]
    education = [x for x in lines if any(k in x.lower() for k in ("education","university","college","bachelor","degree"))]
    experience = [x for x in lines if any(k in x.lower() for k in ("experience","intern","developer","analyst","engineer","project"))]
    return {"education": education[:8], "experience": experience[:8]}

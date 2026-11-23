import re, json
from collections import defaultdict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def tokens(csv_text):
    return [x.strip().lower() for x in (csv_text or "").split(",") if x.strip()]

def recommend(jobs, resume_text, user_skills, interactions, filters=None):
    filters = filters or {}
    documents = [resume_text or " ".join(user_skills)] + [
        f"{j['title']} {j['description']} {j['skills']}" for j in jobs
    ]
    try:
        matrix = TfidfVectorizer(stop_words="english", ngram_range=(1,2), max_features=12000).fit_transform(documents)
        content_scores = cosine_similarity(matrix[0:1], matrix[1:]).flatten()
    except ValueError:
        content_scores = [0.0] * len(jobs)

    history = defaultdict(float)
    for row in interactions:
        # positive preference from save/like; dislike is a negative signal
        history[row["job_id"]] += {"like": 1.0, "save": 0.7, "dislike": -1.0}.get(row["action"], 0)
    user_has_history = bool(interactions)
    alpha = 0.85 if user_has_history else 1.0

    results = []
    for idx, job in enumerate(jobs):
        job_skills = tokens(job["skills"])
        matched = sorted(set(user_skills).intersection(job_skills))
        missing = sorted(set(job_skills) - set(user_skills))
        collab = max(-1, min(1, history.get(job["id"], 0) / 2))
        # Keep content dominant; interaction signal is normalized to [0,1].
        collab01 = (collab + 1) / 2 if user_has_history else 0.5
        score = alpha * float(content_scores[idx]) + (1-alpha) * collab01
        if filters.get("location") and filters["location"].lower() not in (job["location"] or "").lower():
            continue
        if filters.get("job_type") and filters["job_type"] != job["job_type"]:
            continue
        if filters.get("experience") and filters["experience"] != job["experience"]:
            continue
        if filters.get("remote") == "yes" and not job["remote"]:
            continue
        # Blend transparent skill coverage into the displayed score without replacing TF-IDF.
        coverage = len(matched) / max(1, len(job_skills))
        score = 0.75 * score + 0.25 * coverage
        results.append({**dict(job), "score": round(max(0,min(1,score))*100),
                        "matched": matched, "missing": missing,
                        "coverage": round(coverage*100),
                        "reason": ("Matches " + ", ".join(matched[:4])) if matched else
                                  "Related resume wording and role requirements"})
    return sorted(results, key=lambda x: x["score"], reverse=True)

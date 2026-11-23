# Project alignment and next development steps

## Proposal alignment
- Resume upload and parsing: implemented for text-based PDF and DOCX.
- NLP skill extraction: implemented with an editable skill vocabulary and regex matching.
- TF-IDF baseline: implemented using scikit-learn and cosine similarity.
- Semantic Sentence-Transformer model: not enabled by default; add as a separately evaluated model to avoid a large model download on first run.
- Collaborative filtering: lightweight feedback-derived preference signal is implemented as a prototype, not a full KNN/SVD model.
- Hybrid score: implemented with cold-start alpha = 1.0 and alpha = 0.85 once interactions exist.
- Explainability and skill gaps: implemented.
- Filters and feedback: implemented.
- Account registration, login/logout, CSRF protection and per-account profile/feedback storage: implemented for the local prototype.
- PostgreSQL backend selected by `DATABASE_URL`; SQLite remains the local development default.
- Data refresh and live open API integration: not implemented; sample dataset is seeded.
- Evaluation and user study: plan documented; no fabricated measurements.

## Recommended next steps
1. Replace sample jobs with legally obtained open dataset/API records and record source/date.
2. Add an optional Sentence-Transformer model (`all-MiniLM-L6-v2`) and compare against TF-IDF.
3. Implement a proper user/item interaction matrix with enough consenting users before claiming collaborative filtering.
4. Add scheduled data refresh with APScheduler and expired-posting checks.
5. Create a labeled relevance set and calculate Precision@K, Recall@K, MAP and NDCG@K.
6. Run a small consent-based usability study with 10–20 student participants.
7. Before public deployment, add HTTPS, rate limits, account recovery, secure secrets and a documented retention policy; review authentication and data handling.

# PathFinder AI — AI-Powered Job Recommendation System

A Flask web application based on the attached **AI-Powered Job Recommendation System** proposal. It is designed as a runnable final-year-project prototype with a responsive interface, PDF/DOCX resume parsing, skill extraction, explainable job ranking, feedback, saved jobs, filters, and local privacy controls.

## Implemented features

- PDF and DOCX resume upload (5 MB limit), text extraction and a configurable skill dictionary.
- TF-IDF / cosine-similarity content matching and transparent skill-coverage signal.
- Hybrid ranking extension using user feedback (like/save/dislike). With no interaction history, the ranker uses content matching (cold-start behavior).
- Match percentage, matched skills, missing skills, and a short explanation for every recommendation.
- Location, job type, experience and remote filters.
- Save, like and dislike feedback; saved-jobs page.
- Consent requirement, temporary uploaded-file deletion after parsing, and delete-profile/feedback control.
- Email/password account registration, login and logout, with resume profiles and feedback isolated by account.
- SQLite database and sample job listings so the application works immediately without API keys.
- Health endpoint at `/health`.

## Technology / implementation notes

The proposal names Flask, scikit-learn, spaCy, Sentence-Transformers, SQLite/PostgreSQL and APScheduler. This ready-to-run prototype uses Flask, scikit-learn TF-IDF and SQLite locally, and PostgreSQL when `DATABASE_URL` is configured, so it can run on a standard laptop without downloading a large neural model. The skill extractor uses a dictionary and resume text parser. Sentence-Transformer embeddings, live job API integrations, APScheduler refresh, production deployment hardening, and a real student user study are extension work rather than falsely claimed as completed. The interaction-based collaborative signal is a lightweight prototype; early data may be sparse and should be disclosed as such in evaluation.

The included job data is sample/demo data, not a live job feed. Links point to learning resources rather than claiming that each is an active vacancy. Add permitted open-dataset/API records before presenting the system as live.

## Requirements

- Windows 10/11, macOS or Linux
- Python 3.10 or newer
- Visual Studio Code
- Internet connection only for installing Python packages (the app itself runs locally)

## Run in VS Code (Windows)

1. Download and extract the ZIP file.
2. Open VS Code → **File → Open Folder** → select the extracted `ai_job_recommendation_system` folder.
3. Open **Terminal → New Terminal**.
4. Check Python:
   ```powershell
   py --version
   ```
   It should show Python 3.10 or newer. If `py` is unavailable, install Python from https://www.python.org/downloads/ and enable **Add Python to PATH**.
5. Create a virtual environment:
   ```powershell
   py -m venv .venv
   ```
6. Activate it:
   ```powershell
   .venv\Scripts\Activate.ps1
   ```
   If PowerShell blocks activation, run this once in the current terminal, then activate again:
   ```powershell
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   .venv\Scripts\Activate.ps1
   ```
   Or use Command Prompt terminal:
   ```cmd
   .venv\Scripts\activate.bat
   ```
7. Install dependencies:
   ```powershell
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```
8. Start the app:
   ```powershell
   python run.py
   ```
9. Open this address in your browser:
   **http://127.0.0.1:5000**
10. Create an account with your email and a password of at least 8 characters. Use the navigation bar to log in and out.
11. Upload a text-based PDF or DOCX resume, tick the consent checkbox, and choose **Analyze resume**. Review matches and skill gaps. Try filters, Like, Save and Not for me. Open **Saved jobs** to view saved roles.

Set `SECRET_KEY` to a long, random value before running a deployment that needs sessions to survive app restarts. A development key is generated automatically when this environment variable is absent.
When upgrading an existing local database, its previous single-user profile and feedback are assigned to the first account registered.

## Deploy to Vercel

The root `pyproject.toml` configures Vercel to load the Flask app from `run.py` (`run:app`). Add a strong `SECRET_KEY` in the Vercel project's **Settings → Environment Variables**, then redeploy.

Create a managed PostgreSQL database through the Vercel Marketplace (for example, Neon). The app accepts its connection string as either `DATABASE_URL` or Vercel's `POSTGRES_URL`; keep `SECRET_KEY` set for Production and Preview too. The app creates its tables and seeds the sample jobs in the configured database. The database starts with no user accounts; the local SQLite database is not automatically transferred. Locally, the app continues to use SQLite when neither PostgreSQL variable is set.

Uploaded resume files are temporary and written to the system temp directory; extracted profile text is stored in the database after consent. Never commit the real database URL or secret key.

## Run on macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python run.py
```
Then visit (https://ai-job-recommendation-system-4yj5.vercel.app/)

## Troubleshooting

- **`py` or `python` not found:** install Python 3.10+ and restart VS Code.
- **PowerShell script execution is disabled:** use the temporary `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` command above, or activate from Command Prompt.
- **`ModuleNotFoundError`:** activate `.venv` in the VS Code terminal and run `pip install -r requirements.txt` again. Ensure VS Code is using `.venv` (Ctrl+Shift+P → Python: Select Interpreter).
- **PDF produces no text:** the current parser expects a text-based PDF. Scanned/image-only PDFs need OCR before upload.
- **Port 5000 is busy:** change `port=5000` in `run.py` to `port=5001`, then open http://127.0.0.1:5001.
- **Database reset:** stop the server, delete `data/jobs.db`, then run `python run.py`. The database and demo jobs will be recreated.

## Project structure

```text
ai_job_recommendation_system/
├── app/
│   ├── __init__.py
│   ├── auth.py
│   ├── db.py
│   ├── seed.py
│   ├── resume.py
│   ├── recommender.py
│   ├── routes.py
│   ├── templates/
│   │   ├── base.html
│   │   ├── index.html
│   │   └── saved.html
│   └── static/
│       ├── css/style.css
│       └── js/app.js
├── data/
├── uploads/
├── run.py
├── requirements.txt
├── .env.example
└── README.md
```

## How recommendation works

1. Extract text from the resume.
2. Find known skills using the editable vocabulary in `app/resume.py`.
3. Build TF-IDF vectors for the resume and each job description.
4. Calculate cosine similarity.
5. Calculate skill coverage and matched/missing skills.
6. Blend in a small feedback-derived collaborative preference when interactions exist.
7. Apply selected filters and sort descending by final score.

Prototype ranking formula follows the proposal's hybrid concept:

`final_score = α × content_score + (1 − α) × collaborative_score`

For a new user, α is 1.0 (content-only cold start). After feedback exists, α is 0.85. A skill-coverage component is then blended into the displayed score to make skill gaps visible. This is a demonstrator, not a validated production recommender.

## Evaluation plan for your report

The proposal calls for Precision@K, Recall@K, MAP and NDCG@K, comparison of TF-IDF vs embedding vs hybrid, and a 10–20 student user study. These require a labeled resume–job relevance dataset and actual participant feedback. Do not report invented results. Create relevance labels, run the model variants, calculate metrics, and document the sample size and limitations.

## Privacy and responsible use

This prototype stores extracted resume text and skills in a local SQLite database after consent. It deletes the uploaded file after parsing, and **Delete my data** removes the signed-in user's profile and interaction history. Accounts use hashed passwords, CSRF-protected forms, and account-scoped resume/feedback data. The app is still a local academic prototype: add HTTPS, rate limiting, account recovery, secure deployment configuration, a retention policy and a security review before exposing it to the public internet. Recommendations are suggestions, not guarantees. Protected attributes are not intentionally used for matching.

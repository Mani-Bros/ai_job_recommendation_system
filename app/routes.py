import os, json, uuid
from pathlib import Path
from flask import Blueprint, current_app, render_template, request, redirect, url_for, flash, jsonify, session
from werkzeug.utils import secure_filename
from .auth import login_required
from .db import connect
from .resume import extract_text, extract_skills, sections
from .recommender import recommend

bp = Blueprint("main", __name__)
ALLOWED = {".pdf", ".docx"}

def profile():
    with connect() as db:
        row = db.execute(
            "SELECT * FROM profiles WHERE user_id=?", (session["user_id"],)
        ).fetchone()
    return dict(row) if row else {}

def get_jobs():
    with connect() as db:
        return [dict(x) for x in db.execute("SELECT * FROM jobs ORDER BY id DESC")]

def get_interactions(user_id):
    with connect() as db:
        return [dict(x) for x in db.execute(
            "SELECT * FROM interactions WHERE user_id=? ORDER BY id DESC LIMIT 500",
            (user_id,),
        )]

@bp.route("/")
@login_required
def index():
    p = profile()
    skills = json.loads(p.get("skills") or "[]")
    filters = {k: request.args.get(k, "") for k in ("location","job_type","experience","remote")}
    results = recommend(
        get_jobs(), p.get("resume_text", ""), skills,
        get_interactions(session["user_id"]), filters,
    )
    saved = set()
    with connect() as db:
        saved = {r["job_id"] for r in db.execute(
            "SELECT job_id FROM interactions WHERE user_id=? AND action='save'",
            (session["user_id"],),
        )}
    return render_template("index.html", profile=p, skills=skills, results=results,
        filters=filters, saved=saved, total_jobs=len(get_jobs()))

@bp.post("/upload")
@login_required
def upload():
    if request.form.get("consent") != "yes":
        flash("Please confirm consent before uploading your resume.", "error")
        return redirect(url_for("main.index"))
    f = request.files.get("resume")
    if not f or not f.filename:
        flash("Choose a PDF or DOCX resume.", "error")
        return redirect(url_for("main.index"))
    suffix = Path(f.filename).suffix.lower()
    if suffix not in ALLOWED:
        flash("Unsupported file. Upload a PDF or DOCX file.", "error")
        return redirect(url_for("main.index"))
    name = secure_filename(f.filename)
    path = os.path.join(current_app.config["UPLOAD_FOLDER"], f"{uuid.uuid4().hex}{suffix}")
    f.save(path)
    try:
        text = extract_text(path, suffix)
        if not text.strip():
            raise ValueError("No readable text found. If this is a scanned PDF, use an OCR-readable version.")
        skills = extract_skills(text)
        with connect() as db:
            db.execute("""INSERT INTO profiles(user_id,resume_name,resume_text,skills,consent,updated_at)
              VALUES(?,?,?,?,?,CURRENT_TIMESTAMP)
              ON CONFLICT(user_id) DO UPDATE SET resume_name=excluded.resume_name,
              resume_text=excluded.resume_text,skills=excluded.skills,consent=1,updated_at=CURRENT_TIMESTAMP""",
              (session["user_id"], name, text[:100000], json.dumps(skills), 1))
        flash(f"Resume analyzed. Found {len(skills)} skills.", "success")
    except Exception as e:
        flash(f"Could not read resume: {e}", "error")
    finally:
        if os.path.exists(path): os.remove(path)
    return redirect(url_for("main.index"))

@bp.post("/feedback/<int:job_id>")
@login_required
def feedback(job_id):
    action = request.form.get("action")
    if action not in {"like","save","dislike"}:
        return jsonify({"error":"Invalid feedback"}), 400
    with connect() as db:
        if not db.execute("SELECT id FROM jobs WHERE id=?", (job_id,)).fetchone():
            return jsonify({"error":"Job not found"}), 404
        db.execute(
            "INSERT INTO interactions(user_id,job_id,action) VALUES(?,?,?)",
            (session["user_id"], job_id, action),
        )
    flash({"like":"Thanks — preference recorded.","save":"Job saved to your list.","dislike":"Feedback recorded; this helps adjust ranking."}[action], "success")
    return redirect(request.referrer or url_for("main.index"))

@bp.route("/saved")
@login_required
def saved():
    with connect() as db:
        rows = db.execute("""SELECT j.*, i.created_at FROM jobs j JOIN interactions i ON i.job_id=j.id
          WHERE i.user_id=? AND i.action='save' AND i.id=(SELECT MAX(i2.id) FROM interactions i2
          WHERE i2.user_id=? AND i2.job_id=j.id AND i2.action='save')
          ORDER BY i.created_at DESC""",
          (session["user_id"], session["user_id"])).fetchall()
    return render_template("saved.html", jobs=[dict(x) for x in rows])

@bp.post("/delete-data")
@login_required
def delete_data():
    with connect() as db:
        db.execute("DELETE FROM profiles WHERE user_id=?", (session["user_id"],))
        db.execute("DELETE FROM interactions WHERE user_id=?", (session["user_id"],))
    flash("Resume profile and feedback history deleted.", "success")
    return redirect(url_for("main.index"))

@bp.route("/health")
def health():
    return jsonify({"status":"ok","service":"AI Job Recommendation System"})

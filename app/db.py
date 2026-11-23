import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "jobs.db"

@contextmanager
def connect():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        with conn:
            yield conn
    finally:
        conn.close()

def init_db():
    with connect() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          email TEXT NOT NULL UNIQUE COLLATE NOCASE,
          password_hash TEXT NOT NULL,
          created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS profiles (
          user_id INTEGER PRIMARY KEY,
          resume_name TEXT, resume_text TEXT, skills TEXT, consent INTEGER DEFAULT 0,
          updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS jobs (
          id INTEGER PRIMARY KEY, title TEXT NOT NULL, company TEXT NOT NULL,
          location TEXT, job_type TEXT, experience TEXT, remote INTEGER DEFAULT 0,
          description TEXT NOT NULL, skills TEXT NOT NULL, url TEXT, source TEXT DEFAULT 'Sample dataset'
        );
        CREATE TABLE IF NOT EXISTS profile (
          id INTEGER PRIMARY KEY CHECK(id=1), resume_name TEXT, resume_text TEXT,
          skills TEXT, consent INTEGER DEFAULT 0, updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS interactions (
          id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
          job_id INTEGER NOT NULL,
          action TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
          FOREIGN KEY(job_id) REFERENCES jobs(id) ON DELETE CASCADE
        );
        """)
        interaction_columns = {
            row["name"] for row in db.execute("PRAGMA table_info(interactions)")
        }
        if "user_id" not in interaction_columns:
            db.execute(
                "ALTER TABLE interactions ADD COLUMN user_id INTEGER REFERENCES users(id) ON DELETE CASCADE"
            )
        db.execute(
            "CREATE INDEX IF NOT EXISTS interactions_user_action ON interactions(user_id, action)"
        )
        if db.execute("SELECT COUNT(*) FROM jobs").fetchone()[0] == 0:
            from .seed import JOBS

            db.executemany("""INSERT INTO jobs
(title,company,location,job_type,experience,remote,description,skills,url)
VALUES (?,?,?,?,?,?,?,?,?)""", JOBS)

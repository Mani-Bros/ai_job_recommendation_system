import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from app import create_app
from app import db as database


class AuthenticationTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test.db"
        self.db_path_patch = patch.object(database, "DB_PATH", self.db_path)
        self.db_path_patch.start()
        self.app = create_app()
        self.app.config.update(TESTING=True, SECRET_KEY="test-secret")
        self.client = self.app.test_client()

    def tearDown(self):
        self.db_path_patch.stop()
        self.temp_dir.cleanup()

    def csrf_token(self, client):
        with client.session_transaction() as session:
            return session["_csrf_token"]

    def register(self, client, email):
        client.get("/register")
        return client.post(
            "/register",
            data={
                "_csrf_token": self.csrf_token(client),
                "email": email,
                "password": "secure-pass-123",
                "confirm_password": "secure-pass-123",
            },
            follow_redirects=True,
        )

    def test_registration_login_logout_and_protected_pages(self):
        self.assertEqual(self.client.get("/").status_code, 302)
        response = self.register(self.client, "first@example.com")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Discover jobs", response.data)

        with database.connect() as db:
            user = db.execute(
                "SELECT password_hash FROM users WHERE email=?",
                ("first@example.com",),
            ).fetchone()
        self.assertIsNotNone(user)
        self.assertNotEqual(user["password_hash"], "secure-pass-123")

        logout_response = self.client.post(
            "/logout", data={"_csrf_token": self.csrf_token(self.client)}
        )
        self.assertEqual(logout_response.status_code, 302)
        self.assertEqual(self.client.get("/saved").status_code, 302)

        self.client.get("/login")
        login_response = self.client.post(
            "/login",
            data={
                "_csrf_token": self.csrf_token(self.client),
                "email": "FIRST@example.com",
                "password": "secure-pass-123",
            },
            follow_redirects=True,
        )
        self.assertEqual(login_response.status_code, 200)
        self.assertIn(b"Discover jobs", login_response.data)

    def test_duplicate_accounts_and_missing_csrf_are_rejected(self):
        self.register(self.client, "first@example.com")
        self.client.post("/logout", data={"_csrf_token": self.csrf_token(self.client)})
        self.client.get("/register")
        duplicate = self.client.post(
            "/register",
            data={
                "_csrf_token": self.csrf_token(self.client),
                "email": "FIRST@example.com",
                "password": "secure-pass-123",
                "confirm_password": "secure-pass-123",
            },
        )
        self.assertEqual(duplicate.status_code, 200)
        self.assertIn(b"already exists", duplicate.data)
        self.assertEqual(self.client.post("/login").status_code, 400)

    def test_saved_jobs_are_private_to_each_account(self):
        self.register(self.client, "first@example.com")
        self.client.post(
            "/feedback/1",
            data={"_csrf_token": self.csrf_token(self.client), "action": "save"},
        )
        self.assertNotIn(
            b"No saved roles yet", self.client.get("/saved").data
        )

        second_client = self.app.test_client()
        self.register(second_client, "second@example.com")
        self.assertIn(b"No saved roles yet", second_client.get("/saved").data)

    def test_existing_single_user_data_moves_to_first_account_only(self):
        with database.connect() as db:
            db.execute("DROP INDEX interactions_user_action")
            db.execute("ALTER TABLE interactions RENAME TO current_interactions")
            db.execute(
                """CREATE TABLE interactions (
                     id INTEGER PRIMARY KEY AUTOINCREMENT,
                     job_id INTEGER NOT NULL,
                     action TEXT NOT NULL,
                     created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                     FOREIGN KEY(job_id) REFERENCES jobs(id) ON DELETE CASCADE
                   )"""
            )
            db.execute(
                "INSERT INTO interactions(job_id, action) VALUES(1, 'like')"
            )
            db.execute("DROP TABLE current_interactions")
            db.execute(
                "INSERT INTO profile(id, resume_name, resume_text) VALUES(1, ?, ?)",
                ("resume.pdf", "legacy resume text"),
            )
        database.init_db()

        self.register(self.client, "first@example.com")
        with database.connect() as db:
            first_user_id = db.execute(
                "SELECT id FROM users WHERE email='first@example.com'"
            ).fetchone()["id"]
            profile = db.execute(
                "SELECT resume_text FROM profiles WHERE user_id=?",
                (first_user_id,),
            ).fetchone()
            interaction = db.execute(
                "SELECT user_id FROM interactions WHERE action='like'"
            ).fetchone()
        self.assertEqual(profile["resume_text"], "legacy resume text")
        self.assertEqual(interaction["user_id"], first_user_id)

        second_client = self.app.test_client()
        self.register(second_client, "second@example.com")
        self.assertIn(
            b"viewing sample recommendations",
            second_client.get("/").data,
        )

    def test_database_url_is_required_on_vercel(self):
        with patch.dict(
            "os.environ",
            {"VERCEL": "1", "DATABASE_URL": "", "POSTGRES_URL": ""},
        ):
            with self.assertRaisesRegex(RuntimeError, "DATABASE_URL or POSTGRES_URL"):
                with database.connect():
                    pass

    def test_postgres_url_alias_is_supported(self):
        with patch.dict(
            "os.environ",
            {"DATABASE_URL": "", "POSTGRES_URL": "postgresql://example"},
        ):
            self.assertTrue(database.uses_postgres())

    def test_postgres_connection_translates_sqlite_placeholders(self):
        connection = Mock()
        db = database.DatabaseConnection(connection, postgres=True)
        db.execute(
            "SELECT id FROM users WHERE email=?",
            ("person@example.com",),
        )
        connection.execute.assert_called_once_with(
            "SELECT id FROM users WHERE email=%s",
            ("person@example.com",),
        )

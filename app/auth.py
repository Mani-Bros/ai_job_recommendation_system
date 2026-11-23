import hmac
import re
import secrets
import sqlite3
from functools import wraps

from flask import Blueprint, abort, flash, g, redirect, render_template, request, session, url_for
from psycopg import IntegrityError as PostgresIntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from .db import connect, uses_postgres

auth_bp = Blueprint("auth", __name__)


def csrf_token():
    token = session.get("_csrf_token")
    if token is None:
        token = secrets.token_urlsafe(32)
        session["_csrf_token"] = token
    return token


@auth_bp.app_context_processor
def inject_csrf_token():
    return {"csrf_token": csrf_token}


@auth_bp.before_app_request
def load_user_and_check_csrf():
    user_id = session.get("user_id")
    g.user = None
    if user_id is not None:
        with connect() as db:
            g.user = db.execute(
                "SELECT id, email FROM users WHERE id=?", (user_id,)
            ).fetchone()
        if g.user is None:
            session.clear()

    if request.method == "POST":
        submitted_token = request.form.get("_csrf_token", "")
        if not hmac.compare_digest(csrf_token(), submitted_token):
            abort(400, description="The form expired. Reload the page and try again.")


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)

    return wrapped_view


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if g.user is not None:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirmation = request.form.get("confirm_password", "")

        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            flash("Enter a valid email address.", "error")
        elif len(password) < 8:
            flash("Your password must be at least 8 characters.", "error")
        elif password != confirmation:
            flash("The passwords do not match.", "error")
        else:
            try:
                with connect() as db:
                    insert_user = "INSERT INTO users(email, password_hash) VALUES(?, ?)"
                    if uses_postgres():
                        user_id = db.execute(
                            insert_user + " RETURNING id",
                            (email, generate_password_hash(password)),
                        ).fetchone()["id"]
                    else:
                        cursor = db.execute(
                            insert_user,
                            (email, generate_password_hash(password)),
                        )
                        user_id = cursor.lastrowid

                    if (
                        not uses_postgres()
                        and db.execute(
                            "SELECT COUNT(*) AS count FROM users"
                        ).fetchone()["count"] == 1
                    ):
                        legacy_profile = db.execute(
                            "SELECT resume_name, resume_text, skills, consent, updated_at "
                            "FROM profile WHERE id=1"
                        ).fetchone()
                        if legacy_profile:
                            db.execute(
                                """INSERT INTO profiles(
                                     user_id, resume_name, resume_text, skills, consent, updated_at
                                   ) VALUES(?, ?, ?, ?, ?, ?)""",
                                (user_id, *legacy_profile),
                            )
                            db.execute("DELETE FROM profile WHERE id=1")
                        db.execute(
                            "UPDATE interactions SET user_id=? WHERE user_id IS NULL",
                            (user_id,),
                        )
            except (sqlite3.IntegrityError, PostgresIntegrityError):
                flash("An account with that email already exists.", "error")
            else:
                session.clear()
                session["user_id"] = user_id
                flash("Your account is ready.", "success")
                return redirect(url_for("main.index"))

    return render_template("auth.html", mode="register")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if g.user is not None:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        with connect() as db:
            user = db.execute(
                "SELECT id, email, password_hash FROM users WHERE email=?",
                (email,),
            ).fetchone()

        if user is None or not check_password_hash(user["password_hash"], password):
            flash("Incorrect email or password.", "error")
        else:
            session.clear()
            session["user_id"] = user["id"]
            return redirect(url_for("main.index"))

    return render_template("auth.html", mode="login")


@auth_bp.post("/logout")
@login_required
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("auth.login"))

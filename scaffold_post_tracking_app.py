#!/usr/bin/env python3
"""Project scaffolding script for a Flask based postal tracking application.

The script builds a directory tree with boilerplate code following a modular
architecture. It is intentionally minimal yet provides hooks for further
expansion such as authentication, Selenium based tracking and admin panels.

Usage:
    python scaffold_post_tracking_app.py /path/to/new/project
"""

from __future__ import annotations

import argparse
from pathlib import Path
import textwrap

# ---------------------------------------------------------------------------
# File templates
# ---------------------------------------------------------------------------

FILES: dict[str, str] = {
    # Application factory -----------------------------------------------------
    "app/__init__.py": textwrap.dedent('''
        """Application factory for the tracking project."""

        from flask import Flask
        from .extensions import db, login_manager

        def create_app(test_config: dict | None = None) -> Flask:
            """Create and configure a :class:`~flask.Flask` instance."""
            app = Flask(__name__)
            app.config.from_object("app.config.Config")
            if test_config:
                app.config.update(test_config)

            db.init_app(app)
            login_manager.init_app(app)

            # Register blueprints lazily to avoid circular imports
            from . import auth, tracking, admin
            app.register_blueprint(auth.bp)
            app.register_blueprint(tracking.bp)
            app.register_blueprint(admin.bp)
            return app
    '''),
    # Configuration ----------------------------------------------------------
    "app/config.py": textwrap.dedent('''
        """Application configuration objects."""

        import os
        from pathlib import Path

        BASE_DIR = Path(__file__).resolve().parent.parent

        class Config:
            SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
            SQLALCHEMY_DATABASE_URI = (
                os.environ.get("DATABASE_URL") or f"sqlite:///{BASE_DIR/'app.db'}"
            )
            SQLALCHEMY_TRACK_MODIFICATIONS = False
    '''),
    # Extensions --------------------------------------------------------------
    "app/extensions.py": textwrap.dedent('''
        """Instantiate Flask extensions."""

        from flask_sqlalchemy import SQLAlchemy
        from flask_login import LoginManager

        db = SQLAlchemy()
        login_manager = LoginManager()
        login_manager.login_view = "auth.login"
    '''),
    # Models -----------------------------------------------------------------
    "app/models.py": textwrap.dedent('''
        """Database models."""

        from datetime import datetime
        from flask_login import UserMixin
        from werkzeug.security import generate_password_hash, check_password_hash

        from .extensions import db, login_manager


        class User(db.Model, UserMixin):
            id = db.Column(db.Integer, primary_key=True)
            username = db.Column(db.String(80), unique=True, nullable=False)
            email = db.Column(db.String(120), unique=True, nullable=False)
            password_hash = db.Column(db.String(128), nullable=False)
            role = db.Column(db.String(20), default="user")
            created_at = db.Column(db.DateTime, default=datetime.utcnow)

            def set_password(self, password: str) -> None:
                self.password_hash = generate_password_hash(password)

            def check_password(self, password: str) -> bool:
                return check_password_hash(self.password_hash, password)


        @login_manager.user_loader
        def load_user(user_id: str):
            return User.query.get(int(user_id))


        class Tracking(db.Model):
            id = db.Column(db.Integer, primary_key=True)
            user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
            code = db.Column(db.String(64), nullable=False)
            status = db.Column(db.String(20), default="in_transit")
            extracted_json = db.Column(db.Text)
            last_update = db.Column(db.DateTime, default=datetime.utcnow)
            created_at = db.Column(db.DateTime, default=datetime.utcnow)
            screenshot = db.Column(db.String(255))


        class TrackingEvent(db.Model):
            id = db.Column(db.Integer, primary_key=True)
            tracking_id = db.Column(db.Integer, db.ForeignKey("tracking.id"), nullable=False)
            description = db.Column(db.String(255))
            location = db.Column(db.String(255))
            datetime = db.Column(db.DateTime)
    '''),
    # Authentication blueprint ----------------------------------------------
    "app/auth.py": textwrap.dedent('''
        """Authentication routes."""

        from flask import Blueprint, render_template, redirect, url_for, flash, request
        from flask_login import login_user, logout_user, login_required

        from .models import User
        from .extensions import db

        bp = Blueprint("auth", __name__, url_prefix="/auth")

        @bp.route("/login", methods=["GET", "POST"])
        def login():
            if request.method == "POST":
                user = User.query.filter_by(username=request.form["username"]).first()
                if user and user.check_password(request.form["password"]):
                    login_user(user)
                    return redirect(url_for("tracking.dashboard"))
                flash("Invalid credentials", "danger")
            return render_template("auth/login.html")

        @bp.route("/register", methods=["GET", "POST"])
        def register():
            if request.method == "POST":
                user = User(
                    username=request.form["username"],
                    email=request.form["email"],
                )
                user.set_password(request.form["password"])
                db.session.add(user)
                db.session.commit()
                flash("Registration successful. Please log in.", "success")
                return redirect(url_for("auth.login"))
            return render_template("auth/register.html")

        @bp.route("/logout")
        @login_required
        def logout():
            logout_user()
            return redirect(url_for("auth.login"))
    '''),
    # Tracking blueprint -----------------------------------------------------
    "app/tracking.py": textwrap.dedent('''
        """Routes for tracking postal codes."""

        from flask import Blueprint, render_template, request, redirect, url_for
        from flask_login import login_required, current_user

        from .extensions import db
        from .models import Tracking
        from .tracker import fetch_tracking_info

        bp = Blueprint("tracking", __name__)

        @bp.route("/")
        def index():
            return render_template("index.html")

        @bp.route("/dashboard")
        @login_required
        def dashboard():
            trackings = Tracking.query.filter_by(user_id=current_user.id).all()
            return render_template("dashboard.html", trackings=trackings)

        @bp.route("/track", methods=["POST"])
        @login_required
        def track():
            code = request.form["code"].strip()
            info = fetch_tracking_info(code)
            tracking = Tracking(
                user_id=current_user.id,
                code=code,
                status=info["status"],
                extracted_json=str(info),
            )
            db.session.add(tracking)
            db.session.commit()
            return redirect(url_for("tracking.dashboard"))
    '''),
    # Selenium stub ----------------------------------------------------------
    "app/tracker.py": textwrap.dedent('''
        """Selenium based tracker stub."""

        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.chrome.options import Options

        def fetch_tracking_info(code: str) -> dict:
            """Return a basic tracking dictionary using Selenium."""
            options = Options()
            options.add_argument("--headless")
            driver = webdriver.Chrome(options=options)
            try:
                driver.get("https://tracking.post.ir")
                driver.find_element(By.NAME, "txtbSearch").send_keys(code)
                driver.find_element(By.ID, "btnSearch").click()
                driver.implicitly_wait(10)
                html = driver.page_source
                status = "delivered" if "تحویل" in html else "in_transit"
                return {"status": status, "html": html}
            finally:
                driver.quit()
    '''),
    # Admin blueprint --------------------------------------------------------
    "app/admin.py": textwrap.dedent('''
        """Administration views."""

        from flask import Blueprint, render_template
        from flask_login import login_required, current_user

        from .models import User, Tracking

        bp = Blueprint("admin", __name__, url_prefix="/admin")

        @bp.before_request
        def restrict_to_admins():
            if not (current_user.is_authenticated and current_user.role == "admin"):
                return "Forbidden", 403

        @bp.route("/users")
        @login_required
        def users():
            return render_template("admin/users.html", users=User.query.all())

        @bp.route("/trackings")
        @login_required
        def trackings():
            return render_template("admin/trackings.html", trackings=Tracking.query.all())
    '''),
    # Templates --------------------------------------------------------------
    "app/templates/index.html": textwrap.dedent('''
        <!doctype html>
        <html lang="fa" dir="rtl">
        <head>
            <meta charset="utf-8">
            <title>Tracking App</title>
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css">
        </head>
        <body class="p-3">
            <h1>Welcome to the Tracking App</h1>
            <p><a href="{{ url_for('auth.login') }}">Login</a> or <a href="{{ url_for('auth.register') }}">Register</a></p>
        </body>
        </html>
    '''),
    "app/templates/base.html": textwrap.dedent('''
        <!doctype html>
        <html lang="fa" dir="rtl">
        <head>
            <meta charset="utf-8">
            <title>Tracking App</title>
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css">
        </head>
        <body class="container py-4">
            {% with messages = get_flashed_messages(with_categories=true) %}
              {% if messages %}
                {% for category, message in messages %}
                  <div class="alert alert-{{ category }}">{{ message }}</div>
                {% endfor %}
              {% endif %}
            {% endwith %}
            {% block content %}{% endblock %}
        </body>
        </html>
    '''),
    "app/templates/auth/login.html": textwrap.dedent('''
        {% extends "base.html" %}
        {% block content %}
        <h2>Login</h2>
        <form method="post">
            <input name="username" placeholder="Username" class="form-control mb-2">
            <input type="password" name="password" placeholder="Password" class="form-control mb-2">
            <button class="btn btn-primary" type="submit">Login</button>
        </form>
        {% endblock %}
    '''),
    "app/templates/auth/register.html": textwrap.dedent('''
        {% extends "base.html" %}
        {% block content %}
        <h2>Register</h2>
        <form method="post">
            <input name="username" placeholder="Username" class="form-control mb-2">
            <input name="email" placeholder="Email" class="form-control mb-2">
            <input type="password" name="password" placeholder="Password" class="form-control mb-2">
            <button class="btn btn-primary" type="submit">Register</button>
        </form>
        {% endblock %}
    '''),
    "app/templates/dashboard.html": textwrap.dedent('''
        {% extends "base.html" %}
        {% block content %}
        <h2>Your Trackings</h2>
        <form method="post" action="{{ url_for('tracking.track') }}" class="mb-3">
            <div class="input-group">
                <input name="code" placeholder="Tracking code" class="form-control">
                <button class="btn btn-success" type="submit">Track</button>
            </div>
        </form>
        <table class="table table-striped">
            <thead><tr><th>Code</th><th>Status</th><th>Last update</th></tr></thead>
            <tbody>
            {% for t in trackings %}
                <tr><td>{{ t.code }}</td><td>{{ t.status }}</td><td>{{ t.last_update }}</td></tr>
            {% endfor %}
            </tbody>
        </table>
        {% endblock %}
    '''),
    "app/templates/admin/users.html": textwrap.dedent('''
        {% extends "base.html" %}
        {% block content %}
        <h2>Users</h2>
        <table class="table table-striped">
            <thead><tr><th>ID</th><th>Username</th><th>Email</th><th>Role</th></tr></thead>
            <tbody>
            {% for u in users %}
                <tr><td>{{ u.id }}</td><td>{{ u.username }}</td><td>{{ u.email }}</td><td>{{ u.role }}</td></tr>
            {% endfor %}
            </tbody>
        </table>
        {% endblock %}
    '''),
    "app/templates/admin/trackings.html": textwrap.dedent('''
        {% extends "base.html" %}
        {% block content %}
        <h2>All Trackings</h2>
        <table class="table table-striped">
            <thead><tr><th>User</th><th>Code</th><th>Status</th></tr></thead>
            <tbody>
            {% for t in trackings %}
                <tr><td>{{ t.user_id }}</td><td>{{ t.code }}</td><td>{{ t.status }}</td></tr>
            {% endfor %}
            </tbody>
        </table>
        {% endblock %}
    '''),
}

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def write_file(path: Path, content: str) -> None:
    """Write *content* to *path*, creating parent directories as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def scaffold(target: Path) -> None:
    for relative, content in FILES.items():
        write_file(target / relative, content)
    for folder in ["css", "js", "fonts"]:
        (target / "app/static" / folder).mkdir(parents=True, exist_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Create project skeleton")
    parser.add_argument("target", type=Path, help="Target directory for the project")
    args = parser.parse_args()

    target = args.target.resolve()
    if target.exists() and any(target.iterdir()):
        raise SystemExit(f"Target directory {target} is not empty")
    target.mkdir(parents=True, exist_ok=True)

    scaffold(target)
    print(f"Project scaffold created at {target}")


if __name__ == "__main__":
    main()

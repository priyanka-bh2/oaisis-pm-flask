from __future__ import annotations
import os
from datetime import datetime, date
from typing import Optional

from flask import Flask, render_template, redirect, url_for, request, flash, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "app.db")

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

# ----------------------------
# Models
# ----------------------------
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    projects = db.relationship("Project", backref="owner", lazy=True)

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    owner_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    tasks = db.relationship("Task", backref="project", cascade="all, delete-orphan", lazy=True)


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(50), default="Todo")  # Todo, In Progress, Done
    due_date = db.Column(db.Date, nullable=True)
    notes = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    project_id = db.Column(db.Integer, db.ForeignKey("project.id"), nullable=False)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


@app.before_request
def ensure_db():
    # Create tables on first run (simple for MVP)
    with app.app_context():
        db.create_all()

# ----------------------------
# Auth routes
# ----------------------------
@app.route("/", methods=["GET"])
def home():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        if not email or not password:
            flash("Email and password are required.", "danger")
            return redirect(url_for("register"))
        if User.query.filter_by(email=email).first():
            flash("Email already registered. Please log in.", "warning")
            return redirect(url_for("login"))
        user = User(email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash("Account created. Please log in.", "success")
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("dashboard"))
        flash("Invalid credentials.", "danger")
        return redirect(url_for("login"))
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out.", "info")
    return redirect(url_for("home"))

# ----------------------------
# Projects
# ----------------------------
@app.route("/dashboard")
@login_required
def dashboard():
    q = request.args.get("q", "").strip()
    projects_query = Project.query.filter_by(owner_id=current_user.id)
    if q:
        projects_query = projects_query.filter(Project.name.ilike(f"%{q}%"))
    projects = projects_query.order_by(Project.created_at.desc()).all()
    return render_template("dashboard.html", projects=projects, q=q)

@app.route("/projects/new", methods=["GET", "POST"])
@login_required
def project_new():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        description = request.form.get("description") or ""
        if not name:
            flash("Project name is required.", "danger")
            return redirect(url_for("project_new"))
        project = Project(name=name, description=description, owner_id=current_user.id)
        db.session.add(project)
        db.session.commit()
        flash("Project created.", "success")
        return redirect(url_for("dashboard"))
    return render_template("project_form.html", action="Create", project=None)

@app.route("/projects/<int:project_id>")
@login_required
def project_detail(project_id: int):
    project = Project.query.filter_by(id=project_id, owner_id=current_user.id).first_or_404()
    status_filter = request.args.get("status")
    q = request.args.get("q", "").strip()
    tasks_query = Task.query.filter_by(project_id=project.id)
    if status_filter:
        tasks_query = tasks_query.filter(Task.status == status_filter)
    if q:
        tasks_query = tasks_query.filter(Task.title.ilike(f"%{q}%"))
    tasks = tasks_query.order_by(Task.created_at.desc()).all()

    # For simple "board" view group by status
    board = {
        "Todo": [t for t in tasks if t.status == "Todo"],
        "In Progress": [t for t in tasks if t.status == "In Progress"],
        "Done": [t for t in tasks if t.status == "Done"],
    }
    return render_template("project_detail.html", project=project, tasks=tasks, board=board, status_filter=status_filter, q=q)

@app.route("/projects/<int:project_id>/edit", methods=["GET", "POST"])
@login_required
def project_edit(project_id: int):
    project = Project.query.filter_by(id=project_id, owner_id=current_user.id).first_or_404()
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        description = request.form.get("description") or ""
        if not name:
            flash("Project name is required.", "danger")
            return redirect(url_for("project_edit", project_id=project.id))
        project.name = name
        project.description = description
        db.session.commit()
        flash("Project updated.", "success")
        return redirect(url_for("project_detail", project_id=project.id))
    return render_template("project_form.html", action="Update", project=project)

@app.route("/projects/<int:project_id>/delete", methods=["POST"])
@login_required
def project_delete(project_id: int):
    project = Project.query.filter_by(id=project_id, owner_id=current_user.id).first_or_404()
    db.session.delete(project)
    db.session.commit()
    flash("Project deleted.", "info")
    return redirect(url_for("dashboard"))

# ----------------------------
# Tasks
# ----------------------------
@app.route("/projects/<int:project_id>/tasks/new", methods=["GET", "POST"])
@login_required
def task_new(project_id: int):
    project = Project.query.filter_by(id=project_id, owner_id=current_user.id).first_or_404()
    if request.method == "POST":
        title = (request.form.get("title") or "").strip()
        status = request.form.get("status") or "Todo"
        due_date_raw = request.form.get("due_date") or ""
        notes = request.form.get("notes") or ""
        if not title:
            flash("Task title is required.", "danger")
            return redirect(url_for("task_new", project_id=project.id))
        due_date = None
        if due_date_raw:
            try:
                due_date = datetime.strptime(due_date_raw, "%Y-%m-%d").date()
            except ValueError:
                flash("Invalid date format. Use YYYY-MM-DD.", "warning")
        task = Task(title=title, status=status, due_date=due_date, notes=notes, project_id=project.id)
        db.session.add(task)
        db.session.commit()
        flash("Task created.", "success")
        return redirect(url_for("project_detail", project_id=project.id))
    return render_template("task_form.html", action="Create", project=project, task=None)

@app.route("/tasks/<int:task_id>/edit", methods=["GET", "POST"])
@login_required
def task_edit(task_id: int):
    task = Task.query.get_or_404(task_id)
    project = Project.query.filter_by(id=task.project_id, owner_id=current_user.id).first()
    if not project:
        abort(404)
    if request.method == "POST":
        title = (request.form.get("title") or "").strip()
        status = request.form.get("status") or "Todo"
        due_date_raw = request.form.get("due_date") or ""
        notes = request.form.get("notes") or ""
        if not title:
            flash("Task title is required.", "danger")
            return redirect(url_for("task_edit", task_id=task.id))
        due_date = None
        if due_date_raw:
            try:
                due_date = datetime.strptime(due_date_raw, "%Y-%m-%d").date()
            except ValueError:
                flash("Invalid date format. Use YYYY-MM-DD.", "warning")
        task.title = title
        task.status = status
        task.due_date = due_date
        task.notes = notes
        db.session.commit()
        flash("Task updated.", "success")
        return redirect(url_for("project_detail", project_id=project.id))
    return render_template("task_form.html", action="Update", project=project, task=task)

@app.route("/tasks/<int:task_id>/delete", methods=["POST"])
@login_required
def task_delete(task_id: int):
    task = Task.query.get_or_404(task_id)
    project = Project.query.filter_by(id=task.project_id, owner_id=current_user.id).first()
    if not project:
        abort(404)
    db.session.delete(task)
    db.session.commit()
    flash("Task deleted.", "info")
    return redirect(url_for("project_detail", project_id=project.id))

if __name__ == "__main__":
    app.run(debug=True)

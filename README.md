
# OAISIS — Project Management Web App (Flask + SQLite)

A minimal **Project & Task manager** with **auth**, built in Flask. Covers the MVP:

- **Auth**: Sign up / Login / Logout (credentials-based).
- **Projects**: Create, view, update, delete.
- **Tasks**: Create tasks within a project with **title**, **status**, **due date**, **notes**.
- **Storage**: SQLite (file-based persistence).
- **UI**: Simple Bootstrap for clean UX.

> Optional extras included: basic search/filter on tasks, and a lightweight status board view per project.

## Quickstart (Local)

```bash
# 1) Create a virtual environment (optional but recommended)
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 2) Install dependencies
pip install -r requirements.txt

# 3) Initialize the database and create a demo user
python seed.py

# 4) Run the app
python app.py
# App will start at http://127.0.0.1:5000
```

**Demo login:** `demo@demo.com` / `demodemo`  
Or use **Sign Up** to create your own account.

## Tech Choices & Trade-offs

- **Flask + SQLite** for speed and simplicity within 24 hours. SQLite provides durable local persistence with zero setup.
- **Flask-Login** for session management; **werkzeug.security** for password hashing.
- **SQLAlchemy** ORM for quick modeling and migrations-free setup (we create tables at runtime for MVP).
- **Bootstrap via CDN** for quick, clean UI.
- **Scope**: Focused on MVP reliability and clarity rather than advanced patterns.

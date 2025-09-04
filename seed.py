from app import db, User, Project, Task, app
from werkzeug.security import generate_password_hash

with app.app_context():
    db.create_all()

    # Create demo user
    demo_email = "demo@demo.com"
    demo_pass = "demodemo"
    user = User.query.filter_by(email=demo_email).first()
    if not user:
        user = User(email=demo_email)
        user.set_password(demo_pass)
        db.session.add(user)
        db.session.commit()
        print(f"Created demo user: {demo_email} / {demo_pass}")
    else:
        print("Demo user already exists.")

    # Sample project & tasks
    proj = Project.query.filter_by(owner_id=user.id, name="Sample Project").first()
    if not proj:
        proj = Project(name="Sample Project", description="A starter project", owner_id=user.id)
        db.session.add(proj)
        db.session.commit()

        t1 = Task(title="Design schema", status="Todo", project_id=proj.id)
        t2 = Task(title="Build CRUD", status="In Progress", project_id=proj.id)
        t3 = Task(title="Polish UI", status="Done", project_id=proj.id)
        db.session.add_all([t1, t2, t3])
        db.session.commit()
        print("Seeded sample project & tasks.")
    else:
        print("Sample project already exists.")

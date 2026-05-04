from app import app, db, Course, User
from werkzeug.security import generate_password_hash

def sanitize_email(name):
    # e.g. "Dr. Ravi Singh" -> "dr.ravisingh@edulearn.com"
    sanitized = name.lower().replace(" ", "").replace(".", "")
    return f"{sanitized}@edulearn.com"

with app.app_context():
    # 1. Fetch all unique instructor names connected to courses
    course_instructors = db.session.query(Course.instructor).distinct().all()
    names = [i[0] for i in course_instructors if i[0]]

    # 2. Check which users already exist
    created_count = 0
    for name in names:
        # Check if an instructor with this exact name exists
        user = User.query.filter_by(name=name, role='instructor').first()
        if not user:
            # Check if email is already taken
            email = sanitize_email(name)
            if not User.query.filter_by(email=email).first():
                new_user = User(
                    name=name,
                    email=email,
                    password_hash=generate_password_hash('password123'),
                    role='instructor'
                )
                db.session.add(new_user)
                created_count += 1
                print(f"Created instructor account for '{name}' with email '{email}'")
            else:
                print(f"Warning: Email '{email}' for '{name}' already exists. Skipping account creation.")
        else:
            print(f"Account for instructor '{name}' already exists.")

    db.session.commit()
    print(f"\nMigration complete. Successfully provisioned {created_count} instructor accounts.")

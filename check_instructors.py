from app import app, db, Course, User

with app.app_context():
    instructors = db.session.query(Course.instructor).distinct().all()
    print("Instructors in Courses:", [i[0] for i in instructors])
    users = User.query.filter_by(role='instructor').all()
    print("Instructor Users in DB:", [u.name for u in users])

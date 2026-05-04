
# EduLearn – Full Flask Project (Modern UI + Animations)

## Features
- Coursera-style modern look (blue/white palette), glassmorphism cards, hover & scroll animations
- Auth (student/instructor), enrollments, dashboard with animated progress
- **Each course has 10 lessons and 10 quizzes** (auto-generated on seed; 5 questions per quiz)
- Lessons include embedded video & rich HTML content
- Quiz UI with animated progress bar and scoring
- Simple course discussion board

## Run
```bash
python -m venv venv
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
python app.py
```
(Optional) Initialize and seed demo data:
```bash
flask --app app.py initdb
flask --app app.py seed
```
Login:
- Admin:      admin@edulearn.com / admin123
- Instructor: instructor@edulearn.com / password
- Student:    student@edulearn.com / password

Admin dashboard: visit /admin/users after signing in as admin.

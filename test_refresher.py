import os
from dotenv import load_dotenv

from app import app, db, generate_refresher

with app.app_context():
    course_id = 1
    wrong_topics = "What is the keyword to output something to the screen? | How do you comment in Python?"
    res, videos = generate_refresher(course_id, wrong_topics)
    print("RESULT:")
    print(res)

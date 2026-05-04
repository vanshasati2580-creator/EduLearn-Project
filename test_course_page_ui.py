import unittest
from flask import url_for

from app import app, db, User, Course, Lesson, Quiz, Enrollment, Review
from sqlalchemy.pool import StaticPool


class CoursePageUITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Configure test app (in-memory sqlite across connections)
        app.config.update(
            TESTING=True,
            WTF_CSRF_ENABLED=False,
            SQLALCHEMY_DATABASE_URI='sqlite://',
            SQLALCHEMY_ENGINE_OPTIONS={
                'connect_args': {'check_same_thread': False},
                'poolclass': StaticPool
            },
            SERVER_NAME='localhost',
        )
        cls.appctx = app.app_context()
        cls.appctx.push()
        db.create_all()

        # Seed users
        from werkzeug.security import generate_password_hash
        cls.instructor = User(name='UI Instructor', email='ui_instructor@test.com', password_hash=generate_password_hash('password'), role='instructor')
        cls.student = User(name='UI Student', email='ui_student@test.com', password_hash=generate_password_hash('password'), role='student')
        db.session.add_all([cls.instructor, cls.student])
        db.session.commit()

        # Primary course with lessons (one has video preview) and a quiz
        cls.course = Course(title='UI Test Course', short_desc='Short desc for UI tests', long_desc='Long desc', instructor=cls.instructor.name)
        db.session.add(cls.course); db.session.commit()
        lessons = [
            Lesson(course_id=cls.course.id, title='Intro', content='c1', position=1, video_url='https://player.vimeo.com/video/123456789'),
            Lesson(course_id=cls.course.id, title='Chapter 2', content='c2', position=2),
        ]
        db.session.add_all(lessons)
        db.session.add(Quiz(course_id=cls.course.id, title='Quiz 1'))
        db.session.add(Review(course_id=cls.course.id, user_id=cls.student.id, rating=5, comment='Great!'))
        db.session.commit()

        # Related course by same instructor
        cls.related = Course(title='Related UI Course', short_desc='Rel', long_desc='Rel long', instructor=cls.instructor.name)
        db.session.add(cls.related); db.session.commit()

    @classmethod
    def tearDownClass(cls):
        db.session.remove()
        db.drop_all()
        cls.appctx.pop()

    def setUp(self):
        self.client = app.test_client()

    def login(self, email, password):
        return self.client.post('/login', data={'email': email, 'password': password}, follow_redirects=True)

    def test_course_detail_core_elements_anonymous(self):
        # Anonymous user should see hero, sticky CTA shell, share, coupon apply, canonical, related courses
        resp = self.client.get(f'/course/{self.course.id}')
        self.assertEqual(resp.status_code, 200)
        html = resp.data.decode('utf-8', errors='ignore')

        canonical = url_for('course_detail', cid=self.course.id, _external=True)

        # Head/SEO
        self.assertIn('<link rel="canonical"', html)
        self.assertIn(canonical, html)
        self.assertIn('application/ld+json', html)

        # Hero and preview
        self.assertIn('id="course-hero"', html)
        self.assertIn('iframe', html)
        self.assertIn('https://player.vimeo.com/video/123456789', html)

        # Share button and sticky CTA markup
        self.assertIn('class="btn btn-sm btn-outline-secondary rounded-pill js-share"', html)
        self.assertIn('class="sticky-cta js-sticky-cta"', html)

        # Coupon apply button with checkout base URL
        self.assertIn('js-apply-coupon', html)
        # Accept either relative or absolute checkout URL
        self.assertTrue('data-checkout-base="/checkout/' in html or 'data-checkout-base="http://localhost/checkout/' in html)

        # Related courses section shows the related course
        self.assertIn('Related courses', html)
        self.assertIn(self.related.title, html)

    def test_course_detail_enrolled_certificate_and_continue(self):
        # Login and enroll the student, then page should show certificate link and continue learning in sticky CTA
        rv = self.login('ui_student@test.com', 'password')
        self.assertEqual(rv.status_code, 200)

        if not Enrollment.query.filter_by(student_id=self.student.id, course_id=self.course.id).first():
            db.session.add(Enrollment(student_id=self.student.id, course_id=self.course.id))
            db.session.commit()

        page = self.client.get(f'/course/{self.course.id}')
        self.assertEqual(page.status_code, 200)
        html = page.data.decode('utf-8', errors='ignore')

        # Accept either relative or absolute certificate URL
        self.assertTrue('/certificate/' in html or 'http://localhost/certificate/' in html)
        self.assertIn('Get Certificate', html)
        self.assertIn('Continue learning', html)


if __name__ == '__main__':
    unittest.main(verbosity=2)

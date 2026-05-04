import unittest
from urllib.parse import urlparse

from flask import url_for

from app import app, db, User, Course, Lesson, Enrollment, Review, Coupon, enrich_courses
from sqlalchemy.pool import StaticPool


class EduLearnFeatureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Configure app for testing with in-memory SQLite that persists across connections
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
        cls.instructor = User(name='Lead Instructor', email='instructor@test.com', password_hash=User(password_hash='x').password_hash, role='instructor')
        # For tests, generate a real hash via the route helper
        from werkzeug.security import generate_password_hash
        cls.instructor.password_hash = generate_password_hash('password')
        cls.student = User(name='Student Test', email='student@test.com', password_hash=generate_password_hash('password'), role='student')
        db.session.add_all([cls.instructor, cls.student])
        db.session.commit()

        # Seed a course owned by instructor with 3 lessons
        cls.course = Course(title='Test Course', short_desc='Short', long_desc='Long', instructor=cls.instructor.name)
        db.session.add(cls.course); db.session.commit()
        lessons = [
            Lesson(course_id=cls.course.id, title='L1', content='c1', position=1),
            Lesson(course_id=cls.course.id, title='L2', content='c2', position=2),
            Lesson(course_id=cls.course.id, title='L3', content='c3', position=3),
        ]
        db.session.add_all(lessons); db.session.commit()

    @classmethod
    def tearDownClass(cls):
        db.session.remove()
        db.drop_all()
        cls.appctx.pop()

    def setUp(self):
        self.client = app.test_client()

    def login(self, email, password):
        return self.client.post('/login', data={'email': email, 'password': password}, follow_redirects=True)

    def test_review_submission_flow(self):
        # Login as student
        rv = self.login('student@test.com', 'password')
        self.assertEqual(rv.status_code, 200)
        # Enroll the student
        db.session.add(Enrollment(student_id=self.student.id, course_id=self.course.id))
        db.session.commit()
        # Submit a review
        resp = self.client.post(f'/course/{self.course.id}/review', data={'rating': '5', 'comment': 'Great course!'}, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Thanks for your review!', resp.data)
        # Verify DB updated
        r = Review.query.filter_by(course_id=self.course.id, user_id=self.student.id).first()
        self.assertIsNotNone(r)
        self.assertEqual(r.rating, 5)
        # Verify average rating visible on course page
        page = self.client.get(f'/course/{self.course.id}')
        self.assertEqual(page.status_code, 200)
        text = page.data.decode('utf-8', errors='ignore')
        self.assertIn('⭐ 5.0', text)

    def test_lesson_completion_and_certificate_unlock(self):
        # Login as student
        rv = self.login('student@test.com', 'password')
        self.assertEqual(rv.status_code, 200)
        # Enroll
        if not Enrollment.query.filter_by(student_id=self.student.id, course_id=self.course.id).first():
            db.session.add(Enrollment(student_id=self.student.id, course_id=self.course.id))
            db.session.commit()
        # Visit all lessons to update progress
        lessons = Lesson.query.filter_by(course_id=self.course.id).order_by(Lesson.position.asc()).all()
        for l in lessons:
            res = self.client.get(f'/lesson/{l.id}')
            self.assertEqual(res.status_code, 200)
        # Check progress
        e = Enrollment.query.filter_by(student_id=self.student.id, course_id=self.course.id).first()
        total = len(lessons)
        pct = int((e.progress / total) * 100) if total else 0
        self.assertEqual(pct, 100)
        # Certificate should be accessible
        cert = self.client.get(f'/certificate/{self.course.id}', follow_redirects=False)
        self.assertEqual(cert.status_code, 200)
        self.assertIn(b'Certificate of Completion', cert.data)

    def test_instructor_analytics_access(self):
        # Student should be denied
        rv = self.login('student@test.com', 'password')
        self.assertEqual(rv.status_code, 200)
        denied = self.client.get('/instructor/analytics', follow_redirects=False)
        self.assertIn(denied.status_code, (302, 303))
        loc = denied.headers.get('Location', '')
        self.assertIn('/login', loc)  # redirected to login due to instructor_required

        # Instructor should access
        self.client.get('/logout')
        rv2 = self.login('instructor@test.com', 'password')
        self.assertEqual(rv2.status_code, 200)
        ok = self.client.get('/instructor/analytics')
        self.assertEqual(ok.status_code, 200)
        # Should mention at least the instructor's course title
        self.assertIn(self.course.title.encode('utf-8'), ok.data)

    def test_cart_checkout_with_coupon(self):
        # Login as student
        rv = self.login('student@test.com', 'password')
        self.assertEqual(rv.status_code, 200)
        # Create a new course for checkout to avoid prior enrollments
        checkout_course = Course(title='Checkout Course', short_desc='Short c', long_desc='Long c', instructor=self.instructor.name)
        db.session.add(checkout_course); db.session.commit()
        # Create a valid coupon 50% off
        cp = Coupon(code='HALF50', percent_off=50, active=True)
        db.session.add(cp); db.session.commit()
        # Add to cart
        add = self.client.post(f'/cart/add/{checkout_course.id}', follow_redirects=True)
        self.assertEqual(add.status_code, 200)
        # Visit cart with coupon code (not required but simulates user flow)
        cart = self.client.get('/cart?code=HALF50')
        self.assertEqual(cart.status_code, 200)
        # Checkout with valid Luhn card and coupon
        pay = self.client.post('/cart/checkout', data={
            'name': 'Student Test',
            'number': '4242 4242 4242 4242',
            'exp': '12/29',
            'cvv': '123',
            'coupon': 'HALF50'
        }, follow_redirects=True)
        self.assertEqual(pay.status_code, 200)
        # Verify enrollment exists
        e = Enrollment.query.filter_by(student_id=self.student.id, course_id=checkout_course.id).first()
        self.assertIsNotNone(e)
        # Coupon uses incremented
        self.assertEqual(Coupon.query.filter_by(code='HALF50').first().uses, 1)

    def test_registration_login_and_homepage(self):
        # Register a brand new student
        email = 'newstudent@test.com'
        resp = self.client.post('/register', data={
            'name': 'New Student',
            'email': email,
            'password': 'password',
            'role': 'student'
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        text = resp.data.decode('utf-8', errors='ignore')
        self.assertIn('Registration successful', text)
        # Login with the new account
        logged = self.client.post('/login', data={'email': email, 'password': 'password'}, follow_redirects=True)
        self.assertEqual(logged.status_code, 200)
        self.assertIn(b'Welcome back!', logged.data)
        # Visit homepage
        home = self.client.get('/')
        self.assertEqual(home.status_code, 200)
        self.assertIn(b'EduLearn', home.data)

    def test_datasci_default_thumbnail_assignment(self):
        # Create courses: Data Science with generic default, Data Science with custom, and non-DS with generic
        ds_generic = Course(title='Data Science Essentials', short_desc='s', long_desc='l', instructor=self.instructor.name)
        ds_custom = Course(title='Data Science Advanced', short_desc='s', long_desc='l', instructor=self.instructor.name,
                           thumbnail='https://example.com/custom.jpg')
        general_generic = Course(title='Marketing Basics', short_desc='s', long_desc='l', instructor=self.instructor.name)
        db.session.add_all([ds_generic, ds_custom, general_generic])
        db.session.commit()

        # Capture originals for non-DS and custom DS
        ds_custom_before = ds_custom.thumbnail
        general_before = general_generic.thumbnail

        # Run enrichment (idempotent)
        enrich_courses()

        # Reload from DB to ensure changes are persisted
        ds_generic_r = db.session.get(Course, ds_generic.id)
        ds_custom_r = db.session.get(Course, ds_custom.id)
        general_r = db.session.get(Course, general_generic.id)

        DATASCI_DEFAULT = 'https://images.unsplash.com/photo-1556157382-4b8c5d0c7851?q=80&w=1200&auto=format&fit=crop'

        # Assertions
        self.assertEqual(ds_generic_r.thumbnail, DATASCI_DEFAULT)  # DS with generic/missing gets DS default
        self.assertEqual(ds_custom_r.thumbnail, ds_custom_before)  # DS with custom remains unchanged
        self.assertEqual(general_r.thumbnail, general_before)      # Non-DS with generic remains unchanged

        # Idempotency: run again and verify no change
        enrich_courses()
        ds_generic_r2 = db.session.get(Course, ds_generic.id)
        self.assertEqual(ds_generic_r2.thumbnail, DATASCI_DEFAULT)

        # Course detail page should render the DS default thumbnail
        page = self.client.get(f'/course/{ds_generic.id}')
        self.assertEqual(page.status_code, 200)
        # Jinja auto-escapes '&' to '&amp;' within attribute values in HTML
        html = page.data.decode('utf-8', errors='ignore')
        expected_escaped = DATASCI_DEFAULT.replace('&', '&amp;')
        self.assertIn(expected_escaped, html)

    def test_homepage_hero_markup_and_js_includes(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        html = resp.data.decode('utf-8', errors='ignore')
        # Hero container with data-hero for A/B targeting
        self.assertIn('header class="hero', html)
        self.assertIn('data-hero', html)
        # Hero CTA button/link markup exists
        self.assertIn('js-hero-cta', html)
        # Base layout includes app.js so analytics/variant code runs client-side
        self.assertIn('/static/js/app.js', html)


    def test_homepage_datasci_thumbnail_render(self):
        # Create a Data Science course with generic default thumbnail
        ds_home = Course(title='Data Science Bootcamp', short_desc='s', long_desc='l', instructor=self.instructor.name)
        db.session.add(ds_home); db.session.commit()

        # Run enrichment and fetch homepage
        enrich_courses()
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)

        # Expect DS default thumbnail to be present (HTML-escaped)
        DATASCI_DEFAULT = 'https://images.unsplash.com/photo-1556157382-4b8c5d0c7851?q=80&w=1200&auto=format&fit=crop'
        html = resp.data.decode('utf-8', errors='ignore')
        expected_escaped = DATASCI_DEFAULT.replace('&', '&amp;')
        self.assertIn(expected_escaped, html)

if __name__ == '__main__':
    unittest.main(verbosity=2)

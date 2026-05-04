import unittest

from app import app, db
from sqlalchemy.pool import StaticPool


class AboutPageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
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

    @classmethod
    def tearDownClass(cls):
        db.session.remove()
        db.drop_all()
        cls.appctx.pop()

    def setUp(self):
        self.client = app.test_client()

    def test_about_route_and_shiny_names(self):
        resp = self.client.get('/about')
        self.assertEqual(resp.status_code, 200)
        html = resp.data.decode('utf-8', errors='ignore')
        # Headings
        self.assertIn('About EduLearn', html)
        self.assertIn('Meet the Team', html)
        # Exactly three shiny names
        self.assertEqual(html.count('text-shine'), 3)
        # Team member names present
        for name in [
            'Aryan Sanjay Kalmegh',
            'Rahul Kumar Tiwari',
            'Sumit S Khandare',
            'Vansh Asati',
            'Shivam Deshmukh',
            'Snehal Mohod',
        ]:
            self.assertIn(name, html)


if __name__ == '__main__':
    unittest.main(verbosity=2)

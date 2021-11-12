#!/usr/bin/env python
import unittest

from app import create_app, db
from app.models import User, Study
from config import Config


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
    ELASTICSEARCH_URL = None


class UserModelCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_password_hashing(self):
        u = User(username='susan')
        u.set_password('cat')
        self.assertFalse(u.check_password('dog'))
        self.assertTrue(u.check_password('cat'))

    def test_link(self):
        u1 = User(username='kennedy', email='kennedy@example.com')
        s1 = Study(name_study='Kunk', description_study="Whattta.")
        db.session.add(u1)
        db.session.add(s1)
        db.session.commit()

        u1.link(s1)
        db.session.commit()
        self.assertTrue(u1.is_linked(s1))

        u1.unlink(s1)
        db.session.commit()
        self.assertFalse(u1.is_linked(s1))

    def test_follow(self):
        u1 = User(username='john', email='john@example.com')
        u2 = User(username='susan', email='susan@example.com')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        self.assertEqual(u1.followed.all(), [])
        self.assertEqual(u1.followers.all(), [])

        u1.follow(u2)
        db.session.commit()
        self.assertTrue(u1.is_following(u2))
        self.assertEqual(u1.followed.count(), 1)
        self.assertEqual(u1.followed.first().username, 'susan')
        self.assertEqual(u2.followers.count(), 1)
        self.assertEqual(u2.followers.first().username, 'john')

        u1.unfollow(u2)
        db.session.commit()
        self.assertFalse(u1.is_following(u2))
        self.assertEqual(u1.followed.count(), 0)
        self.assertEqual(u2.followers.count(), 0)

    def test_follow_posts(self):
        # create four users
        u1 = User(username='mak', email='mak@example.com')
        u2 = User(username='klak', email='klak@example.com')
        u3 = User(username='mary', email='mary@example.com')
        u4 = User(username='david', email='david@example.com')
        db.session.add_all([u1, u2, u3, u4])

        # create four posts
        s1 = Study(name_study="Klauwen", linked_users=[u1])
        s2 = Study(name_study="Plauwen", linked_users=[u2])
        s3 = Study(name_study="Trouwen", linked_users=[u3])
        s4 = Study(name_study="Snauwen", linked_users=[u4])
        db.session.add_all([s1, s2, s3, s4])
        db.session.commit()

        # setup the followers
        u1.link(s2)  # john follows susan
        u1.link(s4)  # john follows david
        u2.link(s3)  # susan follows mary
        u3.link(s4)  # mary follows david
        db.session.commit()

        # check the followed posts of each user
        f1 = sorted(u1.linked_studies.all())
        f2 = sorted(u2.linked_studies.all())
        f3 = sorted(u3.linked_studies.all())
        f4 = sorted(u4.linked_studies.all())
        self.assertEqual(f1, [s2, s4, s1])
        self.assertEqual(f2, [s2, s3])
        self.assertEqual(f3, [s3, s4])
        self.assertEqual(f4, [s4])


if __name__ == '__main__':
    unittest.main(verbosity=2)
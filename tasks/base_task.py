from celery import Task
from contextlib import contextmanager
from sqlalchemy.exc import OperationalError
from flask import current_app
from context.database import db

class BaseTaskWithDB(Task):
    abstract = True  # Make this an abstract class so it's not registered as a task

    def run(self, *args, **kwargs):
        # This method should be overridden by child classes
        raise NotImplementedError()

    @contextmanager
    def session_scope(self):
        """Provide a transactional scope around a series of operations."""
        with current_app.app_context():
            if not self.check_db_connection(db):
                raise OperationalError("Database connection failed")
            try:
                yield db.session
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                raise self.retry(exc=e)
            finally:
                db.session.remove()

    @staticmethod
    def check_db_connection(db):
        try:
            db.session.execute('SELECT 1')
            return True
        except Exception:
            return False
from celery import Task
from contextlib import contextmanager
from sqlalchemy.exc import OperationalError
from context.database import db
from tools.db_utility import check_db_connection

class BaseTaskWithDB(Task):
    abstract = True  # Make this an abstract class so it's not registered as a task

    def run(self, *args, **kwargs):
        # This method should be overridden by child classes
        raise NotImplementedError()

    @contextmanager
    def session_scope(self):
        from context.app import create_app # Import here to avoid circular imports
        """Provide a transactional scope around a series of operations."""
        app = create_app()  # Create a new Flask app
        with app.app_context():  # Push an app context for Flask
            if not check_db_connection(db):
                raise OperationalError("Database connection failed")
            try:
                yield db.session
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                raise self.retry(exc=e)
            finally:
                db.session.remove()
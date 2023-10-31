from context.app import create_app
from celery import Celery
import os

app = create_app()

def create_test_app():
    app.config['TESTING'] = True
    return app.test_client()

def create_celery_app():
    celery = Celery(__name__, broker=os.environ['REDIS_URL'])
    celery.conf.update(app.config)

    return celery
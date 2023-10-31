from celery import Celery
import os

celery_client = Celery()
celery_client.conf.broker_url = os.environ['REDIS_URL']
from apscheduler.schedulers.gevent import GeventScheduler
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

def job_listener(event):
    if event.exception:
        print(f"Job crashed: {event.exception}")
    else:
        print("Job executed successfully")

scheduler = GeventScheduler()

scheduler.add_listener(job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
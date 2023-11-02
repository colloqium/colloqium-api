web: gunicorn -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker -w 1 main:app
worker: celery -A celery_worker.celery_app worker --loglevel=info -c 2
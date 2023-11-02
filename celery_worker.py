from context.context import create_celery_app

celery_app = create_celery_app()

if __name__ == '__main__':
    celery_app.worker_main()
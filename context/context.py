# context.py
from context.app import create_app

app = create_app()

def create_test_app():
    app.config['TESTING'] = True
    return app.test_client()
from context.context import app, create_celery_app
from context.sockets import socketio
import os

celery_app = create_celery_app()

if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0', port=int(os.environ.get('PORT', 8000)), debug=os.environ.get('FLASK_DEBUG', 'False') == 'True')
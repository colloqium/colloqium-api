import os
from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
from context.database import db
import secrets
from dotenv import load_dotenv
from routes.blueprint import bp
from context.sockets import socketio
from routes.socket_handlers import initialize_socket_handlers
from context.celery import celery_client

def create_app():
    load_dotenv()
    app = Flask(__name__, template_folder='../templates')


    # Get the absolute path of the project directory
    project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
    print(f"Project directory is {project_dir}")

    app.register_blueprint(bp)
    app.config['SECRET_KEY'] = secrets.token_hex(nbytes=8)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_size": 1}

    socketio.init_app(app)
    initialize_socket_handlers()

    CORS(app, resources={r"/*": {"origins": "*"}})
    app.config['CORS_HEADERS'] = 'Content-Type'

    app.config['CELERY_BROKER_URL'] = os.environ['REDIS_URL']
    celery_client.conf.update(app.config)

    db.init_app(app)
    Migrate(app, db)

    with app.app_context():
        db.engine.execution_options(isolation_level="SERIALIZABLE")

    
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db.session.remove()
    
    return app
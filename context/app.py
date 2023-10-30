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
from context.scheduler import scheduler

def create_app():
    load_dotenv()
    app = Flask(__name__, template_folder='../templates')


    # Get the absolute path of the project directory
    project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
    print(f"Project directory is {project_dir}")

    # Set the STATIC_FOLDER configuration to the "static" directory in the project directory
    static_folder = os.path.join(project_dir, 'static')

    app.config['STATIC_FOLDER'] = static_folder

    print(f"Static folder is {app.config['STATIC_FOLDER']}")

    
    app.register_blueprint(bp)
    app.config['SECRET_KEY'] = secrets.token_hex(nbytes=8)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_size": 1000}

    socketio.init_app(app)
    initialize_socket_handlers()

    CORS(app, resources={r"/*": {"origins": "*"}})
    app.config['CORS_HEADERS'] = 'Content-Type'

    db.init_app(app)
    Migrate(app, db)

    with app.app_context():
        db.engine.execution_options(isolation_level="SERIALIZABLE")

    return app

# def setup_migrations(app, db):
#     db.session.close_all()

#     # setup migrations
#     Migrate(app, db)

#     # check if migrations folder does not exists, then initialize
#     if not os.path.exists('migrations'):
#         # Create a migrations folder and the initial migration
#         with app.app_context():
#             os.mkdir('migrations')
#             upgrade()

#     # Run the migration and apply it to the database
#     with app.app_context():
#         upgrade()
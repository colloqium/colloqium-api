import os
from flask import Flask
from flask_migrate import Migrate, upgrade
from context.database import db
import secrets
from dotenv import load_dotenv
from routes.blueprint import bp
from context.constants import STATIC_FOLDER

def create_app():
    load_dotenv()
    app = Flask(__name__, template_folder='../templates')
    
    app.register_blueprint(bp)
    app.config['SECRET_KEY'] = secrets.token_hex(nbytes=8)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL'] 
    app.config['STATIC_FOLDER'] = STATIC_FOLDER

    db.init_app(app)
    with app.app_context():
        setup_migrations(app, db)

    return app

def setup_migrations(app, db):
    db.session.close_all()

    # setup migrations
    Migrate(app, db)

    # check if migrations folder does not exists, then initialize
    if not os.path.exists('migrations'):
        # Create a migrations folder and the initial migration
        with app.app_context():
            os.mkdir('migrations')
            upgrade()

    # Run the migration and apply it to the database
    with app.app_context():
        upgrade()
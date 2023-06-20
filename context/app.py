import shutil
from flask import Flask
from flask_migrate import Migrate, upgrade, init
from context.database import db
import secrets
from dotenv import load_dotenv
from routes.blueprint import bp
import os
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
        reset_database(app, db)

    return app

def reset_database(app, db):
    db.session.close_all()
    db.drop_all()
    
    # check if migrations folder exists
    if os.path.exists('migrations'):
        shutil.rmtree('migrations')
        
        # create migrations folder
    os.mkdir('migrations')

    Migrate(app, db)
    init()
    upgrade()
    db.create_all()
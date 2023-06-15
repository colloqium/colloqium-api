from flask import Flask
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from context.database import db
import secrets
from dotenv import load_dotenv
from routes.blueprint import bp
import os


def create_app():
    load_dotenv()
    app = Flask(__name__, template_folder='../templates')
    app.register_blueprint(bp)
    app.config['SECRET_KEY'] = secrets.token_hex(nbytes=8)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']

    db.init_app(app)

    with app.app_context():
        db.drop_all()  # first delete all tables
        db.create_all()  # then create all tables
        Migrate(app, db)  # initialize Flask-Migrate

    return app
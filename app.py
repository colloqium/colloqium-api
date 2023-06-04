from flask import Flask
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from database import db
import secrets


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = secrets.token_hex(nbytes=8)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'

    db.init_app(app)

    with app.app_context():
        db.create_all()  # Create all tables
        Migrate(app, db)  # initialize Flask-Migrate

    csrf_protect = CSRFProtect()
    csrf_protect.init_app(app)

    return app, csrf_protect

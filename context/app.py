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
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
    db_path = os.path.join(os.getcwd(), '../instance/site.db')

    db.init_app(app)

    with app.app_context():
        if os.path.exists(db_path):  # check if db file exists
            os.remove(db_path)  # if it does, remove it
        db.create_all()  # then create all tables
        Migrate(app, db)  # initialize Flask-Migrate

    return app
from context.database import db
from models.models import Recipient, Sender, Interaction, Audience, Campaign, PhoneNumber
from flask import Flask
from dotenv import load_dotenv
import secrets
import os

def init_db():
    load_dotenv()
    app = Flask(__name__)

    app.config['SECRET_KEY'] = secrets.token_hex(nbytes=8)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']

    db.init_app(app)


    with app.app_context():
        if not db.inspect(db.engine).get_table_names():
            db.drop_all()
            db.create_all()

if __name__ == "__main__":
    init_db()

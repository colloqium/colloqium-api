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

    from sqlalchemy import inspect

    with app.app_context():
        inspector = inspect(db.engine)
        table_names = inspector.get_table_names()
        if table_names:
            meta = db.metadata
            for table in reversed(meta.sorted_tables):
                if table.name in table_names:
                    print(f"Dropping table {table}")
                    db.session.execute(table.delete())
            db.session.commit()
        Migrate(app, db)  # initialize Flask-Migrate
        db.create_all()  # then create all tables

    return app
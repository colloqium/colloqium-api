from flask_wtf.csrf import CSRFProtect
from flask import current_app


with current_app.app_context():
    csrf_protect = CSRFProtect()
    csrf_protect.init_app(current_app)
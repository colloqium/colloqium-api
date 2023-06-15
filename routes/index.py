from flask import Blueprint
# import Flask and other libraries
from flask import redirect, url_for

index_bp = Blueprint('index', __name__)

@index_bp.route("/", methods=['GET', 'POST'])
def index():
    return redirect(
        url_for('bp.interaction', last_action="LoadingServerForTheFirstTime"))
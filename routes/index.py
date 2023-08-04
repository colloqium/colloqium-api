from flask import Blueprint
# import Flask and other libraries

index_bp = Blueprint('index', __name__)

@index_bp.route("/", methods=['GET', 'POST'])
def index():
    return 'Colloqium API'
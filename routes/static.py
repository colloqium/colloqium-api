from flask import Flask, Blueprint, send_from_directory
from context.constants import STATIC_FOLDER
import os

static = Blueprint('static', __name__)


@static.route('/static/js/<filename>')
def send_js(filename):
    return send_from_directory(os.path.join(STATIC_FOLDER, 'js'), filename)
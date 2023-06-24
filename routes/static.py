from flask import send_file, current_app as app
import os

def static(path):
    print("inside static")
    return send_file(os.path.join(app.config['STATIC_FOLDER'], path))
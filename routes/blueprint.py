from flask import Blueprint

# Import the routes from the separate files
from routes.twilio_call import twilio_call
from routes.twilio_message import twilio_message
from routes.index import index
from routes.interaction import interaction
from routes.call import call
from routes.text_message import text_message
from routes.plan import plan
from routes.confirm_messages import confirm_messages
from routes.twilio_message_callback import twilio_message_callback
from routes.static import send_js

bp = Blueprint('bp', __name__)
print("Registering routes")

# Register the routes with the blueprint
bp.add_url_rule("/twilio_call", view_func=twilio_call, methods=['POST'])
bp.add_url_rule("/twilio_message", view_func=twilio_message, methods=['POST'])
bp.add_url_rule("/", view_func=index, methods=['GET', 'POST'])
bp.add_url_rule("/interaction/<last_action>", view_func=interaction, methods=['GET', 'POST'])
bp.add_url_rule("/call/<interaction_id>", view_func=call, methods=['POST'])
bp.add_url_rule("/text_message/<interaction_id>", view_func=text_message, methods=['POST'])
bp.add_url_rule("/plan/<int:recipient_id>", view_func=plan, methods=['POST'])
bp.add_url_rule("/<int:sender_id>/confirm_messages", view_func=confirm_messages, methods=['GET', 'POST'])
bp.add_url_rule("/twilio_message_callback", view_func=twilio_message_callback, methods=['POST'])

# add a url for static/js/<filename> to serve the javascript files
bp.add_url_rule('/static/js/<filename>', endpoint='static/js', view_func=send_js)
from flask import Blueprint

# Import the routes from the separate files
from routes.twilio_call import twilio_call
from routes.twilio_message import twilio_message
from routes.index import index
from routes.interaction import interaction
from routes.call import call
from routes.text_message import text_message
from routes.plan import plan

bp = Blueprint('bp', __name__)

# Register the routes with the blueprint
bp.add_url_rule("/twilio_call", view_func=twilio_call, methods=['POST'])
bp.add_url_rule("/twilio_message", view_func=twilio_message, methods=['POST'])
bp.add_url_rule("/", view_func=index, methods=['GET', 'POST'])
bp.add_url_rule("/interaction/<last_action>", view_func=interaction, methods=['GET', 'POST'])
bp.add_url_rule("/call/<interaction_id>", view_func=call, methods=['POST'])
bp.add_url_rule("/text_message/<interaction_id>", view_func=text_message, methods=['POST'])
bp.add_url_rule("/plan/<int:recipient_id>", view_func=plan, methods=['POST'])
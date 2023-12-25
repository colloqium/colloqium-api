from flask import Blueprint

# Import the routes from the separate files
from routes.inbound_message import inbound_message
from routes.index import index
from routes.interaction import interaction
from routes.send_text import send_text
from routes.make_robo_call import make_robo_call
from routes.send_email import send_email
from routes.interaction_callback import interaction_callback
from routes.sender import sender
from routes.voter import voter
from routes.campaign import campaign
from routes.alert import alert
from routes.campaign_insights import campaign_insights
from routes.audience import audience

bp = Blueprint('bp', __name__)
print("Registering routes")

# Register the routes with the blueprint
bp.add_url_rule("/inbound_message", view_func=inbound_message, methods=['POST'])
bp.add_url_rule("/", view_func=index, methods=['GET', 'POST'])
bp.add_url_rule("/interaction", view_func=interaction, methods=['GET', 'POST', 'PUT', 'DELETE'])
bp.add_url_rule("/send_text", view_func=send_text, methods=['POST', 'OPTIONS'])
bp.add_url_rule("/make_robo_call", view_func=make_robo_call, methods=['POST', 'OPTIONS'])
bp.add_url_rule("/send_email", view_func=send_email, methods=['POST', 'OPTIONS'])
bp.add_url_rule("/interaction_callback", view_func=interaction_callback, methods=['POST'])
bp.add_url_rule("/sender", view_func=sender, methods=['GET', 'POST', 'PUT'])
bp.add_url_rule("/voter", view_func=voter, methods=['GET', 'POST', 'PUT', 'OPTIONS'])
bp.add_url_rule("/campaign", view_func=campaign, methods=['GET', 'POST', 'PUT', 'DELETE'])
bp.add_url_rule("/alert", view_func=alert, methods=['GET', 'PUT'])
bp.add_url_rule("/campaign/insights", view_func=campaign_insights, methods=['PUT'])
bp.add_url_rule("/audience", view_func=audience, methods=['GET', 'POST', 'PUT', 'DELETE'])
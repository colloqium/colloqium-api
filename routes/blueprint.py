from flask import Blueprint

# Import the routes from the separate files
from routes.inbound_call import inbound_call
from routes.inbound_text import inbound_message
from routes.index import index
from routes.interaction import interaction
from routes.call import call
from routes.send_text import send_text
from routes.plan import plan
from routes.confirm_messages import confirm_messages
from routes.twilio_message_callback import twilio_message_callback
from routes.sender import sender
from routes.recipient import recipient
from routes.campaign import campaign
from routes.audience import audience
from routes.static import static

bp = Blueprint('bp', __name__)
print("Registering routes")

# Register the routes with the blueprint
bp.add_url_rule("/inbound_call", view_func=inbound_call, methods=['POST'])
bp.add_url_rule("/inbound_message", view_func=inbound_message, methods=['POST'])
bp.add_url_rule("/", view_func=index, methods=['GET', 'POST'])
bp.add_url_rule("/interaction", view_func=interaction, methods=['GET', 'POST', 'PUT', 'DELETE'])
bp.add_url_rule("/call/", view_func=call, methods=['POST'])
bp.add_url_rule("/send_text", view_func=send_text, methods=['POST', 'OPTIONS'])
bp.add_url_rule("/plan/<int:recipient_id>", view_func=plan, methods=['POST'])
bp.add_url_rule("/<int:sender_id>/confirm_messages", view_func=confirm_messages, methods=['GET', 'POST'])
bp.add_url_rule("/twilio_message_callback", view_func=twilio_message_callback, methods=['POST'])
bp.add_url_rule('/static_files/<path:path>', view_func=static, methods=['GET'])
bp.add_url_rule("/sender", view_func=sender, methods=['GET', 'POST', 'PUT'])
bp.add_url_rule("/recipient", view_func=recipient, methods=['GET', 'POST', 'PUT', 'OPTIONS'])
bp.add_url_rule("/campaign", view_func=campaign, methods=['GET', 'POST', 'PUT', 'DELETE'])
bp.add_url_rule("/audience", view_func=audience, methods=['GET', 'POST', 'PUT', 'DELETE'])
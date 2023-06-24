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
from routes.static import static

bp = Blueprint('bp', __name__)
print("Registering routes")

# Register the routes with the blueprint
bp.add_url_rule("/inbound_call", view_func=inbound_call, methods=['POST'])
bp.add_url_rule("/inbound_message", view_func=inbound_message, methods=['POST'])
bp.add_url_rule("/", view_func=index, methods=['GET', 'POST'])
bp.add_url_rule("/interaction/<last_action>", view_func=interaction, methods=['GET', 'POST'])
bp.add_url_rule("/call/", view_func=call, methods=['POST'])
bp.add_url_rule("/send_text/", view_func=send_text, methods=['POST'])
bp.add_url_rule("/plan/<int:recipient_id>", view_func=plan, methods=['POST'])
bp.add_url_rule("/<int:sender_id>/confirm_messages", view_func=confirm_messages, methods=['GET', 'POST'])
bp.add_url_rule("/twilio_message_callback", view_func=twilio_message_callback, methods=['POST'])
bp.add_url_rule('/static_files/<path:path>', view_func=static, methods=['GET'])
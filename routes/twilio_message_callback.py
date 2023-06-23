# URL to handle twilio status callbacks
from flask import Blueprint, request, jsonify
from models.models import Recipient, Interaction, Sender
from context.analytics import analytics, EVENT_OPTIONS

twilio_message_callback_bp = Blueprint('twilio_message_callback', __name__)

@twilio_message_callback_bp.route('/twilio_message_callback', methods=['POST'])
def twilio_message_callback():
    print(f"Twilio Callback Request")

    # Get the 'From' number from the incoming request
    from_number = request.values.get('From', None)
    to_number = request.values.get('To', None)
    status = request.values.get('MessageStatus', None)  
    
    analytics.track(from_number, EVENT_OPTIONS.interaction_call_back, {
                'recipient_phone_number': to_number,
                'interaction_type': 'text_message',
                'status': status
            })

    return jsonify({'success': True}), 200
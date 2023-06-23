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
    sender_phone_number = request.values.get('To', None)
    status = request.values.get('Status', None) 

    recipient = Recipient.query.filter_by(recipient_phone_number=from_number).first()
    if not recipient:
        analytics.track(from_number, EVENT_OPTIONS.interaction_call_back, {
            'interaction_type': 'text_message',
            'recipient_phone_number': from_number,
            'sender_phone_number': sender_phone_number,
            'status': 'no_recipient_found'
        })
        print("No recipient found")
        return jsonify({'status': 'error', 'message': 'No recipient found'}), 404


    sender = Sender.query.filter_by(sender_phone_number=sender_phone_number).first()
    
    # If the recipient exists, find the Interaction for this recipient with type 'text'
    interaction = Interaction.query.filter_by(
        recipient_id=recipient.id, sender_id=sender.id, interaction_type='text_message').first()
    if interaction is None:
        print("No interaction found")
        analytics.track(recipient.id, EVENT_OPTIONS.interaction_call_back, {
            'interaction_type': 'text_message',
            'recipient_phone_number': from_number,
            'sender_phone_number': sender_phone_number,
            'status': 'no_interaction_found'
        })
        return jsonify({
            'status': 'error',
            'last_action': 'no_interaction_found'
        }), 200
    
    analytics.track(recipient.id, EVENT_OPTIONS.interaction_call_back, {
                'interaction_id': interaction.id,
                'recipient_name': recipient.recipient_name,
                'recipient_phone_number': recipient.recipient_phone_number,
                'sender_name': sender.sender_name,
                'sender_phone_number': sender.sender_phone_number,
                'interaction_type': interaction.interaction_type,
                'status': status
            })
    



    return "OK"
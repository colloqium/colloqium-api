# URL to handle twilio status callbacks
from flask import Blueprint, request, jsonify
from models.models import Recipient, Interaction, Sender
from context.analytics import analytics, EVENT_OPTIONS

twilio_message_callback_bp = Blueprint('twilio_message_callback', __name__)

@twilio_message_callback_bp.route('/twilio_message_callback', methods=['POST'])
def twilio_message_callback():
    print("Twilio Callback Request:")
    print(request.values.to_dict)

    # Get the 'From' number from the incoming request
    from_number = request.values.get('From', None)
    to_number = request.values.get('To', None)
    status = request.values.get('MessageStatus', None)
    # get sender with from number
    sender = Sender.query.filter_by(sender_phone_number=from_number).first()

    
    if sender:
        # get recipient with to number
        recipient = Recipient.query.filter_by(recipient_phone_number=to_number).first()

        # get the interaction
        interaction = Interaction.query.filter_by(sender=sender, recipient=recipient, interaction_type="text_message").first()

        analytics.track(recipient.id, EVENT_OPTIONS.interaction_call_back, {
                    'status': status,
                    'interaction_id': interaction.id,
                    'interaction_type': interaction.interaction_type,
                    'recipient_name': recipient.recipient_name,
                    'recipient_phone_number': recipient.recipient_phone_number,
                    'sender_name': sender.sender_name,
                    'sender_phone_number': sender.sender_phone_number,
                })

    return jsonify({'success': True}), 200
# URL to handle twilio status callbacks
from flask import Blueprint, request, jsonify
from models.models import Recipient, Interaction, InteractionStatus
from models.model_utility import get_phone_number_from_db
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
    
    
    # find the PhoneNumber object for the from number
    phone_number = get_phone_number_from_db(from_number)
    
    if  not phone_number:
        return jsonify({'status': 'error', 'message': "Sender number not found in our system"}), 400
    
    sender = phone_number.sender


    # get recipient with to number
    recipient = Recipient.query.filter_by(recipient_phone_number=to_number).first()

    if not recipient:
        return jsonify({'status': 'error', 'message': 'No recipient found'}), 400

    # Use SqlAlchemy to query the database for the interaction that was created most recently
    interaction = Interaction.query.filter_by(recipient_id=recipient.id).order_by(Interaction.created_at.desc()).first()

    if not interaction:
        return jsonify({'status': 'error', 'message': 'No interaction found'}), 400
    
    # update the interaction status
    if status == 'sent':
        interaction.status = InteractionStatus.SENT
    if status == 'delivered':
        interaction.status = InteractionStatus.DELEIVERED

    analytics.track(recipient.id, EVENT_OPTIONS.interaction_call_back, {
                'status': status,
                'interaction_id': interaction.id,
                'interaction_type': interaction.interaction_type,
                'recipient_name': recipient.recipient_name,
                'recipient_phone_number': recipient.recipient_phone_number,
                'sender_name': sender.sender_name,
                'sender_phone_number': phone_number.get_full_phone_number(),
            })

    return jsonify({'status': 'success'}), 200
# URL to handle twilio status callbacks
from flask import Blueprint, request, jsonify, Response
from models.voter import Voter
from models.interaction import Interaction, InteractionStatus
from tools.db_utility import get_phone_number_from_db
from context.analytics import analytics, EVENT_OPTIONS
from context.database import db
from logs.logger import logger
from twilio.twiml.messaging_response import MessagingResponse

twilio_message_callback_bp = Blueprint('twilio_message_callback', __name__)

@twilio_message_callback_bp.route('/twilio_message_callback', methods=['POST'])
def twilio_message_callback():
    logger.info("Twilio Callback Request:")
    print("Twilio Callback Request:")

    #the resquest is a application/x-www-form-urlencoded type post.
    # Extract the values form the request:
    #   SmsSid: SM2xxxxxx
    #   SmsStatus: sent
    #   MessageStatus: sent
    #   To: +1512zzzyyyy
    #   MessageSid: SM2xxxxxx
    #   AccountSid: ACxxxxxxx
    #   From: +1512xxxyyyy
    #   ApiVersion: 2010-04-01

    # Get the 'From' number from the incoming request
    from_number = request.values.get('From', None)
    to_number = request.values.get('To', None)
    status = request.values.get('MessageStatus', None)

    response = Response(str(MessagingResponse()), mimetype='application/xml')
    
    
    # find the PhoneNumber object for the from number
    phone_number = get_phone_number_from_db(from_number)
    
    if  not phone_number:

        logger.error(f"Phone number {from_number} not found in database")
        return response, 400
    
    sender = phone_number.sender


    # get voter with to number
    voter = Voter.query.filter_by(voter_phone_number=to_number).first()

    if not voter:
        logger.error(f"voter not found for phone number {to_number}")
        return response, 400
    
    if not sender:
        logger.error(f"sender not found for phone number {from_number}")
        return response, 400

    # Use SqlAlchemy to query the database for the interaction that was created most recently and matches the sender id
    interaction = Interaction.query.filter_by(voter_id=voter.id, sender_id=sender.id).order_by(Interaction.time_created.desc()).first()

    if not interaction:
        logger.error(f"No interaction found for voter {voter.voter_name} and sender {sender.sender_name}")
        return response, 400
    
    # update the interaction status
    if status == 'sent':
        print("Message sent")
        if interaction.interaction_status < InteractionStatus.SENT:
            interaction.interaction_status = InteractionStatus.SENT
    if status == 'delivered':
        print("Message delivered")
        if interaction.interaction_status < InteractionStatus.DELIVERED:
            interaction.interaction_status = InteractionStatus.DELIVERED

    analytics.track(voter.id, EVENT_OPTIONS.interaction_call_back, {
                'status': status,
                'interaction_id': interaction.id,
                'interaction_type': interaction.interaction_type,
                'voter_name': voter.voter_name,
                'voter_phone_number': voter.voter_phone_number,
                'sender_name': sender.sender_name,
                'sender_phone_number': phone_number.get_full_phone_number(),
            })
    
    db.session.add(interaction)
    db.session.commit()

    return response, 200
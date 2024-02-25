# URL to handle twilio status callbacks
from flask import Blueprint, request, Response
from models.voter import Voter
from models.interaction import Interaction
from tools.db_utility import get_phone_number_from_db
from logs.logger import logger
from twilio.twiml.messaging_response import MessagingResponse
from tasks.process_twilio_callback import process_twilio_callback

interaction_callback_bp = Blueprint('interaction_callback', __name__)

@interaction_callback_bp.route('/interaction_callback', methods=['POST'])
def interaction_callback():
    logger.info("Interaction Callback Request:")
    print("Interaction Callback Request:")

    # Get the 'From' number from the incoming request
    from_number = request.values.get('From', None)
    to_number = request.values.get('To', None)

    # should only be one of these
    status = request.values.get('MessageStatus', None)

    if not status:
        status = request.values.get('CallStatus', None)

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
    
    process_twilio_callback.apply_async(args=[interaction.id, status, phone_number.id])

    return response, 200
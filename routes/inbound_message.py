from flask import Blueprint
# import Flask and other libraries
from flask import request, Response
from models.interaction import Interaction
from models.voter import Voter
from tools.db_utility import get_phone_number_from_db
# from logs.logger import logging
from twilio.twiml.messaging_response import MessagingResponse
from logs.logger import logger
from tasks.process_inbound_message import process_inbound_message

inbound_message_bp = Blueprint('inbound_message', __name__)

@inbound_message_bp.route("/inbound_message", methods=['POST'])
def inbound_message():
    print("Inbound message received")

    # Get the 'From' number from the incoming request
    from_number = request.values.get('From', None)
    sender_phone_number = request.values.get('To', None)
    message_body = request.values.get('Body', None)

    response = Response(str(MessagingResponse()), mimetype='application/xml')

    print(f"From: {from_number} To: {sender_phone_number}")

    # Use the 'From' number to look up the voter in your database
    voter = Voter.query.filter_by(
        voter_phone_number=from_number).first()

    # If the voter doesn't exist, create a new one and a new Interaction
    if not voter:
        
        logger.error(f"voter not found for phone number {from_number}")
        print("No voter found")
        return response, 400
    
    
    print(f"voter: {voter.voter_name}")

    # get the phone number object for this number from the database
    phone_number = get_phone_number_from_db(sender_phone_number)

    if phone_number is None:
        # return an http error indicating that the phone number is not in the database

        logger.error(f"Phone number {sender_phone_number} not found in database")
        return response, 400
    
    sender = phone_number.sender
    print(f"Sender: {sender.sender_name}")

    # get the interaction associated with this texting agent, campaign, voter, and the most recent time_created
    interaction = Interaction.query.filter(Interaction.agent_id.isnot(None), Interaction.campaign_id.isnot(None), Interaction.sender_id==sender.id, Interaction.voter_id==voter.id).order_by(Interaction.time_created.desc()).first()

    if not interaction:
        print("No interaction found")
        return response, 400
    
    process_inbound_message.apply_async(args=[interaction.id, message_body, sender_phone_number])
 
    return response, 200
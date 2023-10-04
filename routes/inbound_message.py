import datetime
from flask import Blueprint, current_app
# import Flask and other libraries
from flask import request, Response
from models.interaction import Interaction, InteractionStatus, SenderVoterRelationship
from models.voter import Voter
from models.sender import Sender
from models.model_utility import get_phone_number_from_db
from tools.utility import add_message_to_conversation, get_llm_response_to_conversation
# from logs.logger import logging
from context.database import db
from context.apis import client, message_webhook_url, twilio_messaging_service_sid
from context.analytics import analytics, EVENT_OPTIONS
from context.scheduler import scheduler
from twilio.twiml.messaging_response import MessagingResponse
from logs.logger import logger

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
    interaction = Interaction.query.filter_by(sender_id=sender.id, voter_id=voter.id).order_by(Interaction.time_created.desc()).first()

    interaction.interaction_status = InteractionStatus.RESPONDED
    
    # Now you can add the new message to the conversation
    logger.info(f"Recieved message message body: {message_body}")
    # print(f"Recieved message body: {message_body}")
    analytics.track(voter.id, EVENT_OPTIONS.recieved, {
                'interaction_id': interaction.id,
                'voter_name': voter.voter_name,
                'voter_phone_number': voter.voter_phone_number,
                'sender_name': sender.sender_name,
                'sender_phone_number': sender_phone_number,
                'interaction_type': interaction.interaction_type,
                'message': message_body,
            })


    # get the planning agent for this campaign and voter
    relationship = SenderVoterRelationship.query.filter_by(voter_id=voter.id, sender_id=sender.id).first()
    # filter the relationship.agents for an agent with the name planning_agent
    planning_agent = list(filter(lambda agent: agent.name == "planning_agent", relationship.agents))[0]

    # send the message to the planning agent
    planning_agent.send_prompt({
        "content": f"Recieved a reply from the voter, generate a response if appropriate. Campaign ID is {interaction.campaign_id}. Voter ID is {voter.id}. If not, end the conversation.: {message_body}",
    })

    db.session.add(interaction)
    db.session.commit()
 
    return response, 200
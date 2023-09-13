import datetime
from flask import Blueprint, current_app
# import Flask and other libraries
from flask import request, Response
from models.interaction import Interaction, InteractionStatus
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



def send_message(message_body, sender_phone_number, voter_id, sender_id, interaction_id, app):

    with app.app_context():
        voter = Voter.query.get(voter_id)
        sender = Sender.query.get(sender_id)
        interaction = Interaction.query.get(interaction_id)

        print(f"Message called at {datetime.datetime.now()}")
        client.messages.create(
                    body=message_body['content'],
                    from_=sender_phone_number,
                    status_callback=message_webhook_url,
                    to=voter.voter_phone_number,
                    messaging_service_sid=twilio_messaging_service_sid)
        
        analytics.track(voter.id, EVENT_OPTIONS.sent, {
                    'interaction_id': interaction.id,
                    'voter_name': voter.voter_name,
                    'voter_phone_number': voter.voter_phone_number,
                    'sender_name': sender.sender_name,
                    'sender_phone_number': sender_phone_number,
                    'message': message_body,
                })


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
    
    # If the voter exists, find the Interaction for this voter with type 'text' that was created most recently
    interaction = Interaction.query.filter_by(sender_id=sender.id, voter_id=voter.id, interaction_type='text_message').order_by(Interaction.time_created.desc()).first()
    if interaction is None:
        print("No interaction found")
        logger.error(f"No interaction found for voter {voter.voter_name} and sender {sender.sender_name}")
        return response, 400
    
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


    interaction.conversation = add_message_to_conversation(interaction.conversation, message_body)
    
    logger.info(
        f"Conversation after including message: {interaction.conversation}")
    # generate a new response from openAI to continue the conversation
    message_body = get_llm_response_to_conversation(interaction.conversation)
    print(f"AI message: {message_body['content']}")

    interaction.conversation.append(message_body)


    logger.info(f"Conversation after adding LLM response: {interaction.conversation}")
    # print(f"Conversation after adding LLM response: {interaction.conversation}")

    db.session.add(interaction)
    db.session.commit()

    print(f"Message scheduled at {datetime.datetime.now()}")
    scheduler.add_job(func=send_message, kwargs={"message_body": message_body, "sender_phone_number": sender_phone_number, "voter_id": voter.id, "sender_id": sender.id, "interaction_id": interaction.id, "app": current_app._get_current_object()}, trigger='date', run_date=datetime.datetime.now() + datetime.timedelta(seconds=15))
    
    # Check if scheduler is running
    if not scheduler.running:
        print("Starting scheduler")
        scheduler.start()
 
    return response, 200
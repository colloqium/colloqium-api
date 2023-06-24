from flask import Blueprint
# import Flask and other libraries
from flask import request, jsonify
from models.models import Recipient, Sender, Campaign, Interaction
from prompts.campaign_volunteer_agent import get_campaign_text_message_system_prompt
from tools.utility import add_message_to_conversation, add_llm_response_to_conversation, initialize_conversation
# from logs.logger import logging
from datetime import date, timedelta
from context.database import db
from context.apis import client, base_url
from context.analytics import analytics, EVENT_OPTIONS


inbound_message_bp = Blueprint('inbound_message', __name__)

@inbound_message_bp.route("/inbound_message", methods=['POST'])
def inbound_message():
    print("Inbound message received")

    # Get the 'From' number from the incoming request
    from_number = request.values.get('From', None)
    sender_phone_number = request.values.get('To', None)
    message_body = request.values.get('Body', None)

    print(f"From: {from_number} To: {sender_phone_number}")

    # Use the 'From' number to look up the recipient in your database
    recipient = Recipient.query.filter_by(
        recipient_phone_number=from_number).first()

    # If the recipient doesn't exist, create a new one and a new Interaction
    if not recipient:
        
        print("No recipient found")
        recipient = Recipient(recipient_name='',
                              recipient_phone_number=from_number)
        db.session.add(recipient)

        campaign = Campaign()

        campaign.campaign_end_date=date.today() + timedelta(days=1)
        campaign.campaign_name="Help Find Correct Campaign"
        campaign.campaign_information="The user reaching out to you is not associated with a campaign. Can you find out who they expect to reach"

        interaction = Interaction(twilio_conversation_sid='',
                                  interaction_type="text_message",
                                  recipient=recipient,
                                  campaign = campaign,
        sender = Sender()
                )

        system_prompt = get_campaign_text_message_system_prompt(interaction)

        # Create a new conversation with a system message
        conversation = initialize_conversation(system_prompt)
        interaction.conversation = conversation

        analytics.track(from_number, EVENT_OPTIONS.recieved, {
                'interaction_id': interaction.id,
                'recipient_phone_number': from_number,
                'interaction_type': interaction.interaction_type,
                'message': message_body,
            })

        db.session.add(interaction)
    else:
        print(f"Recipient: {recipient.recipient_name}")
        
        sender = Sender.query.filter_by(sender_phone_number=sender_phone_number).first()
        print(f"Sender: {sender.sender_name}")
        
        # If the recipient exists, find the Interaction for this recipient with type 'text'
        interaction = Interaction.query.filter_by(
            recipient_id=recipient.id, sender_id=sender.id, interaction_type='text_message').first()
        if interaction is None:
            print("No interaction found")
            return jsonify({
                'status': 'error',
                'last_action': 'no_interaction_found'
            }), 200

    
    
    # Now you can add the new message to the conversation
    print(f"Recieved message body: {message_body}")
    analytics.track(recipient.id, EVENT_OPTIONS.recieved, {
                'interaction_id': interaction.id,
                'recipient_name': recipient.recipient_name,
                'recipient_phone_number': recipient.recipient_phone_number,
                'sender_name': sender.sender_name,
                'sender_phone_number': sender.sender_phone_number,
                'interaction_type': interaction.interaction_type,
                'message': message_body,
            })


    interaction.conversation = add_message_to_conversation(
        interaction, message_body)
    
    callback_route = base_url + "twilio_message_callback"

    print(
        f"Conversation after including message: {interaction.conversation}")
    # generate a new response from openAI to continue the conversation
    message_body = add_llm_response_to_conversation(interaction)
    print(f"AI message: {message_body}")



    print(
        f"Conversation after adding LLM response: {interaction.conversation}")

    db.session.add(interaction)
    db.session.commit()

    client.messages.create(
                body=message_body,
                from_=sender_phone_number,
                status_callback=callback_route,
                to=recipient.recipient_phone_number)
    
    analytics.track(recipient.id, EVENT_OPTIONS.sent, {
                'interaction_id': interaction.id,
                'recipient_name': recipient.recipient_name,
                'recipient_phone_number': recipient.recipient_phone_number,
                'sender_name': sender.sender_name,
                'sender_phone_number': sender.sender_phone_number,
                'message': message_body,
            })
    
    return jsonify({
                'status': 'success',
                'last_action':
                f"Sending text to {recipient.recipient_name} at {recipient.recipient_phone_number}",
                'Message': message_body,
            }), 200
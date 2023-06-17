from flask import Blueprint
# import Flask and other libraries
from flask import request, jsonify
from models.models import Recipient, Sender, Campaign, Interaction
from prompts.campaign_volunteer_agent import get_campaign_text_message_system_prompt
from tools.utility import add_message_to_conversation, add_llm_response_to_conversation, initialize_conversation
from logs.logger import logging
from datetime import date, timedelta
from context.database import db
from context.apis import client, twilio_number


twilio_message_bp = Blueprint('twilio_message', __name__)

@twilio_message_bp.route("/twilio_message", methods=['POST'])
def twilio_message():
    logging.debug(request.get_data())

    # Get the 'From' number from the incoming request
    from_number = request.values.get('From', None)
    sender_phone_number = request.values.get('To', None)

    # Use the 'From' number to look up the recipient in your database
    recipient = Recipient.query.filter_by(
        recipient_phone_number=from_number).first()

    # If the recipient doesn't exist, create a new one and a new Interaction
    if not recipient:
        recipient = Recipient(recipient_name='',
                              recipient_phone_number=from_number)
        db.session.add(recipient)

        campaign = Campaign()

        campaign.campaign_end_date=date.today() + timedelta(days=1)
        campaign.campaign_name="Help Find Correct Campaign"
        campaign.campaign_information="The user reaching out to you is not associated with a campaign. Can you find out who they expect to reach"

        interaction = Interaction(twilio_conversation_sid='',
                                  interaction_type='text',
                                  recipient=recipient,
                                  campaign = campaign,
        sender = Sender()
                )

        system_prompt = get_campaign_text_message_system_prompt(interaction)

        # Create a new conversation with a system message
        conversation = initialize_conversation(system_prompt)
        interaction.conversation = conversation

        db.session.add(interaction)
    else:
        sender = Sender.query.filter_by(sender_phone_number=sender_phone_number).first()
        # If the recipient exists, find the Interaction for this recipient with type 'text'
        interaction = Interaction.query.filter_by(
            recipient_id=recipient.id, sender_id=sender.id, interaction_type='text').first()

    # Now you can add the new message to the conversation
    message_body = request.values.get('Body', None)
    logging.info(f"Recieved message body: {message_body}")
    interaction.conversation = add_message_to_conversation(
        interaction, message_body)

    logging.debug(
        f"Conversation after including message: {interaction.conversation}")
    # generate a new response from openAI to continue the conversation
    message_body = add_llm_response_to_conversation(interaction)
    logging.debug(f"AI message: {message_body}")
    logging.debug(
        f"Conversation after adding LLM response: {interaction.conversation}")

    db.session.add(interaction)
    db.session.commit()

    client.messages.create(
                body=message_body,
                from_=sender_phone_number,
                to=recipient.recipient_phone_number)
    
    return jsonify({
                'status': 'success',
                'last_action':
                f"Sending text to {recipient.recipient_name} at {recipient.recipient_phone_number}",
                'Message': message_body,
            }), 200
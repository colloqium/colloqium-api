from flask import Blueprint, request, jsonify
import csv
# import Flask and other libraries
from flask import render_template, session
from forms.interaction_form import InteractionForm
from models.models import Recipient, Sender, Campaign, Interaction
from prompts.campaign_volunteer_agent import get_campaign_phone_call_system_prompt, get_campaign_text_message_system_prompt
from prompts.campaign_planner_agent import get_campaign_agent_system_prompt
from tools.utility import add_llm_response_to_conversation, initialize_conversation
from logs.logger import logger, logging
from context.database import db
# Import the functions from the other files
from routes.call import call
from routes.text_message import text_message
from routes.plan import plan
import io


interaction_bp = Blueprint('interaction', __name__)


@interaction_bp.route('/interaction/<last_action>', methods=['GET', 'POST'])
def interaction(last_action):
    try:
        logger.info("Processing Interaction form...")

        # Create instance of recipientCallForm class
        form = InteractionForm()

        # When the form is submitted
        if form.validate_on_submit():
            # If a CSV file was uploaded
            if 'recipient_csv' in request.files:

                file = form.recipient_csv.data
                text_file = io.TextIOWrapper(file, encoding='utf-8')
                csv_data = csv.reader(text_file, delimiter=',')

                # We expect the first row to be headers, so we get those first
                headers = next(csv_data)

                interactions = []

                # Then we process each row in the CSV
                for row in csv_data:
                    # We create a dictionary where the keys are the CSV headers and the values are the row's values
                    recipient_data = {headers[i]: value for i, value in enumerate(row)}

                    # Then we use this dictionary to create a recipient
                    recipient_name = recipient_data['Recipient Name']
                    recipient_information = recipient_data['Recipient Information']
                    recipient_phone_number = recipient_data['Phone Number']
    
                    # Check if a recipient with the given name and phone number already exists
                    recipient = Recipient.query.filter_by(
                        recipient_name=recipient_name,
                        recipient_phone_number=recipient_phone_number).first()

                    # If the recipient does not exist, create a new one
                    if not recipient:
                        recipient = Recipient(
                            recipient_name=recipient_name,
                            recipient_phone_number=recipient_phone_number,
                            recipient_information=recipient_information)
                        db.session.add(recipient)

                    # Check if sender with this name is in database
                    sender = Sender.query.filter_by(
                        sender_name=form.sender_name.data).first()

                    if not sender:
                        sender = Sender(
                            sender_name=form.sender_name.data,
                            sender_information=form.sender_information.data)
                        db.session.add(sender)

                    # Check if campaign wiht this name is in database
                    campaign = Campaign.query.filter_by(
                        campaign_name=form.campaign_name.data).first()

                    if not campaign:
                        campaign = Campaign(
                            campaign_name=form.campaign_name.data,
                            campaign_information=form.campaign_information.data,
                            campaign_end_date=form.campaign_end_date.data)
                        db.session.add(campaign)

                    interaction_type = form.interaction_type.data

                    # Create the Interaction
                    interaction = Interaction(
                        twilio_conversation_sid='',  # You will need to update this later
                        conversation=[],
                        recipient=recipient,  # The ID of the recipient
                        sender=sender,
                        campaign=campaign,
                        interaction_type=interaction_type)

                    db.session.add(interaction)
                    db.session.commit()

                    #get interaction with DB fields
                    interaction = db.session.query(Interaction).filter_by(
                        recipient_id=recipient.id,
                        interaction_type=interaction_type,
                        campaign_id=campaign.id).first()
                    
                    interactions.append(interaction)

                for interaction in interactions:
                    
                    interaction_type = interaction.interaction_type
                    if interaction_type == "call":
                        # Add information from recipientCallForm to the system prompt
                        system_prompt = get_campaign_phone_call_system_prompt(
                            interaction)
                    elif interaction_type == "text":
                        system_prompt = get_campaign_text_message_system_prompt(
                            interaction)
                    elif interaction_type == "plan":
                        system_prompt = get_campaign_agent_system_prompt(interaction)

                    user_number = interaction.recipient.recipient_phone_number

                    #Pre create the first response
                    conversation = initialize_conversation(system_prompt)
                    interaction.conversation = conversation
                    initial_statement = add_llm_response_to_conversation(interaction)
                    logging.info("Interaction created successfully")

                    db.session.commit()

                    # Log the system prompt and user number
                    logging.info("Interaction Type: %s", interaction_type)
                    logging.info(f"System prompt: {system_prompt}")
                    logging.info(f"User number: {user_number}")
                    logging.info(f"Initial Statement: {initial_statement}")
                    logging.debug(f"Conversation: {conversation}")

                    # Store data in session
                    session[
                        'interaction_id'] = interaction.id  # Store the interaction ID

                    if (interaction_type == "call"):
                        # Call the recipient
                        logging.info("Redirecting to call route...")
                        call(interaction_id=interaction.id)
                    elif (interaction_type == "text"):
                        # Send a text message
                        logging.info("Redirecting to text message route...")
                        text_message(interaction_id=interaction.id)
                    elif (interaction_type == "plan"):
                        # Create an outreach agent and plan the outreach for the recipient
                        logging.info("Redirecting to planning route...")
                        plan(recipient_id=recipient.id)     
                
                return jsonify({'success': True}), 200
            else:
                logging.info(f"No form submitted. Error: {form.errors}")
                return render_template('interaction.html',
                                    form=form,
                                    last_action=last_action)
        return render_template('interaction.html', form=form, last_action=last_action)

    except Exception as e:
        logger.error(f"Exception occurred: {e}", exc_info=True)
        return render_template('interaction.html',
                               form=form,
                               last_action="Error")
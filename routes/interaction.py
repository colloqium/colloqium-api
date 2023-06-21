from flask import Blueprint, request, redirect, url_for, current_app
import csv
# import Flask and other libraries
from flask import render_template
from forms.interaction_form import InteractionForm
from models.models import Recipient, Sender, Campaign, Interaction, InteractionStatus
from context.constants import INTERACTION_TYPES
from tools.utility import add_llm_response_to_conversation, initialize_conversation, format_phone_number
from context.database import db
from logs.logger import logger
# Import the functions from the other files
import io


interaction_bp = Blueprint('interaction', __name__)

@interaction_bp.route('/interaction/<last_action>', methods=['GET', 'POST'])
def interaction(last_action):
    try:
        print("Processing Interaction form...")
        logger.info("Processing Interaction form...")

        # Create instance of InteractionForm class
        form = InteractionForm()

        # When the form is submitted
        if form.validate_on_submit():
            
            # The CSV file should have a header row and the following columns:
            # - Recipient Name: The name of the recipient
            # - Recipient Information: Additional information about the recipient (facts about the recipient, etc.)
            # - Phone Number: The phone number of the recipient (in E.164 format)
            # Example:
            # Recipient Name,Recipient Information,Phone Number
            # John Doe,John has never voted as a tech enthusist who lives in GA,+14155552671
            # Jane Smith,Jane has recently become a US citizen and cares about animal rights,jane.smith@example.com,+14155552672
            
            # If a CSV file was uploaded
            if 'recipient_csv' in request.files:

                # Read the CSV data from the uploaded file
                file = form.recipient_csv.data
                text_file = io.TextIOWrapper(file, encoding='utf-8')
                csv_data = csv.reader(text_file, delimiter=',')

                # We expect the first row to be headers, so we get those first
                headers = next(csv_data)

                interactions = []

                # Then we process each row in the CSV
                for row in csv_data:
                    # Create an interaction from the row
                    interaction = create_interaction_from_csv_row(headers, row, form)
                    print(f"Created Interaction: {interaction}")
                    interactions.append(interaction)

                # Process each interaction
                for interaction in interactions:
                    initialize_interaction(interaction)
                    print(f"Initialized Interaction: {interaction.id}")
                
                sender = Sender.query.get(interaction.sender_id)
                #reroute to the confirm messages page
                return redirect(url_for('bp.confirm_messages', sender_id=sender.id))
            else:
                print(f"No form subdmitted. Error: {form.errors}")
                return render_template('interaction.html',
                                    form=form,
                                    last_action=last_action)
        return render_template('interaction.html', form=form, last_action='create_interaction')

    except Exception as e:
        print(f"Exception occurred: {e}", exc_info=True)
        return render_template('interaction.html',
                               form=form,
                               last_action="Error")
    

def create_interaction_from_csv_row(headers, row, form) -> Interaction:
    # We create a dictionary where the keys are the CSV headers and the values are the row's values
    recipient_data = {headers[i]: value for i, value in enumerate(row)}

    # Then we use this dictionary to create a recipient
    recipient_name = recipient_data['Recipient Name']
    recipient_information = recipient_data['Recipient Information']
    recipient_phone_number = format_phone_number(recipient_data['Phone Number'])
    print(f"Recipient phone number from CSV: {recipient_phone_number}")

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
            sender_information=form.sender_information.data,
            sender_phone_number=form.sender_phone_number.data)
        db.session.add(sender)

    # Check if campaign with this name is in database
    campaign = Campaign.query.filter_by(
        campaign_name=form.campaign_name.data).first()

    if not campaign:
        campaign = Campaign(
            campaign_name=form.campaign_name.data,
            campaign_information=form.campaign_information.data,
            campaign_end_date=form.campaign_end_date.data)
        db.session.add(campaign)

    # access the name field of the InteractionType object represented by the slelection in the form. Make it lower case and replace spaces with underscores
    interaction_type = form.interaction_type.data.lower().replace(" ", "_")

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

    # Get interaction with DB fields
    interaction = db.session.query(Interaction).filter_by(
        recipient_id=recipient.id,
        interaction_type=interaction_type,
        campaign_id=campaign.id, sender_id=sender.id).first()

    return interaction

# Creates a new interaction with a recipient and the first system message in the conversation. Does not send the message.
def initialize_interaction(interaction):
    interaction_type = interaction.interaction_type

    system_prompt = INTERACTION_TYPES[interaction_type].system_initialization_method(interaction)

    user_number = interaction.recipient.recipient_phone_number
    sender_number = interaction.sender.sender_phone_number

    # Pre-create the first response
    conversation = initialize_conversation(system_prompt)
    interaction.conversation = conversation
    initial_statement = add_llm_response_to_conversation(interaction)
    print("Interaction created successfully")
    interaction.interaction_status = InteractionStatus.INITIALIZED

    db.session.commit()

    # Log the system prompt and user number
    print("Interaction Type: %s", interaction_type)
    print(f"System prompt: {system_prompt}")
    print(f"User number: {user_number}")
    print(f"Sender number: {sender_number}")
    print(f"Initial Statement: {initial_statement}")
    print(f"Conversation: {conversation}")
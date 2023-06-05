# import Flask and other libraries
from flask import Response, render_template, request, redirect, url_for, session, jsonify
from twilio.twiml.voice_response import VoiceResponse
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
import os
import openai
from forms.interaction_form import InteractionForm
from models import Recipient, Sender, Campaign, Interaction
from prompts.campaign_volunteer_agent import get_campaign_phone_call_system_prompt, get_campaign_text_message_system_prompt
from prompts.campaign_planner_agent import get_campaign_agent_system_prompt
from tools.campaign_agent_tools import CampaignTools, extract_action, execute_action
from tools.utility import add_message_to_conversation, add_llm_response_to_conversation, initialize_conversation
from tools.scheduler import scheduler
from logs.logger import logger, logging
from datetime import date, timedelta
from database import db
from context import app, csrf_protect

# Your Twilio account credentials
account_sid = os.environ['twilio_account_sid']
auth_token = os.environ['twilio_auth_token']
twilio_number = os.environ['twilio_number']

# The webhook URL for handling the call events
call_webhook_url = os.environ['CALL_WEBHOOK_URL']

# Create a Twilio client object
client = Client(account_sid, auth_token)

# set OpenAi Key for GPT4
openai.api_key = os.environ['OPENAI_API_KEY']


# Define a route for handling Twilio webhook requests
@app.route("/twilio_call", methods=['GET', 'POST'])
@csrf_protect.exempt
def twilio_call():
    try:
        logging.info("Twilio Phone Call Request Received")
        logging.info(request.get_data())
        call_id = request.form['CallSid']
        logging.info("Call id: " + call_id)
        interaction = Interaction.query.filter_by(
            twilio_conversation_sid=call_id).first()

        # Retrieve the conversation from our 'database' using the CallSid
        conversation = interaction.conversation

        # If conversation does not exist, log an error and return
        if not conversation:
            logging.error('Could not retrieve conversation from database.')
            return Response('Failed to retrieve conversation.', status=500)

        # Retrieve the speech result from the Twilio request
        speech_result = request.values.get('SpeechResult', None)

        response = VoiceResponse()

        # Add the user's message to the conversation
        if speech_result:
            add_message_to_conversation(interaction, speech_result)
            # Log the user's message to the console
            logger.info(f"User message: {speech_result}")

            # Get the AI response and add it to the conversation
            try:
                text = add_llm_response_to_conversation(interaction)
            except:
                text = "Sorry, I am having trouble hearing you. I will try to call again later, Goodbye"
            conversation.append({"role": "assistant", "content": text})
        else:
            # This is the first message and you can just use the completion
            text = conversation[-1]['content']

        logger.info(f"AI message: {text}")

        # Return the response as XML
        response.say(text)

        #check if text contains "goodbye", if so, hang up the call, other wise continue gathering input
        if "goodbye" in text.lower():
            response.hangup()
            logging.info("Goodbye message received, hanging up call")
        else:
            response.gather(input="speech",
                            action=call_webhook_url,
                            method="POST")
            logging.info("Gathering input from user")

        response_xml = response.to_xml()

        logging.info('Response successfully created and returned.')
        db.session.commit()
        return Response(response_xml, content_type="text/xml")

    except Exception as e:
        # Log the exception
        logging.exception('An error occurred while processing the request: %s',
                          e)
        # Return a server error response
        return Response('An error occurred while processing the request.',
                        status=500)


@app.route("/twilio_message", methods=['GET', 'POST'])
@csrf_protect.exempt
def twilio_message():
    logging.debug(request.get_data())

    # Get the 'From' number from the incoming request
    from_number = request.values.get('From', None)

    # Use the 'From' number to look up the recipient in your database
    recipient = Recipient.query.filter_by(
        recipient_phone_number=from_number).first()

    # If the recipient doesn't exist, create a new one and a new Interaction
    if not recipient:
        recipient = Recipient(recipient_name='',
                              recipient_phone_number=from_number)
        db.session.add(recipient)

        system_prompt = get_campaign_text_message_system_prompt(
            recipient, Sender(),
            Campaign(
                campaign_end_date=date.today() + timedelta(days=1),
                campaign_name="Help Find Correct Campaign",
                campaign_information=
                "The user reaching out to you is not associated with a campaign. Can you find out who they expect to reach"
            ))

        # Create a new conversation with a system message
        conversation = initialize_conversation(system_prompt)

        interaction = Interaction(twilio_conversation_sid='',
                                  conversation=conversation,
                                  interaction_type='text',
                                  recipient_id=recipient.id)
        db.session.add(interaction)
    else:
        # If the recipient exists, find the Interaction for this recipient with type 'text'
        interaction = Interaction.query.filter_by(
            recipient_id=recipient.id, interaction_type='text').first()

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
                from_=twilio_number,
                to=recipient.recipient_phone_number)
    
    return jsonify({
                'status': 'success',
                'last_action':
                f"Sending text to {recipient.recipient_name} at {recipient.recipient_phone_number}",
                'Message': message_body,
            }), 200


@app.route("/", methods=['GET', 'POST'])
@csrf_protect.exempt
def home():
    return redirect(
        url_for('interaction', last_action="LoadingServerForTheFirstTime"))


@app.route('/interaction/<last_action>', methods=['GET', 'POST'])
@csrf_protect.exempt
def interaction(last_action):
    try:
        app.logger.info("Processing Interaction form...")

        # Create instance of recipientCallForm class
        form = InteractionForm()

        # When the form is submitted
        if form.validate_on_submit():
            # Check if a recipient with the given name and phone number already exists
            recipient = Recipient.query.filter_by(
                recipient_name=form.recipient_name.data,
                recipient_phone_number=form.recipient_phone_number.data).first(
                )

            # If the recipient does not exist, create a new one
            if not recipient:
                recipient = Recipient(
                    recipient_name=form.recipient_name.data,
                    recipient_phone_number=form.recipient_phone_number.data,
                    recipient_information=form.recipient_information.data)
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
                    campaign_information=form.campaign_information.data)
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

            if interaction_type == "call":
                # Add information from recipientCallForm to the system prompt
                system_prompt = get_campaign_phone_call_system_prompt(
                    interaction)
            elif interaction_type == "text":
                system_prompt = get_campaign_text_message_system_prompt(
                    interaction)
            elif interaction_type == "plan":
                system_prompt = get_campaign_agent_system_prompt(interaction)

            user_number = form.recipient_phone_number.data

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
                return redirect(url_for('call'), interaction_id=interaction.id)
            elif (interaction_type == "text"):
                # Send a text message
                logging.info("Redirecting to text message route...")
                return redirect(
                    url_for('text_message', interaction_id=interaction.id))
            elif (interaction_type == "plan"):
                # Create an outreach agent and plan the outreach for the recipient
                logging.info("Redirecting to planning route...")
                return redirect(url_for('plan', recipient_id=recipient.id))

        return render_template('interaction.html',
                               form=form,
                               last_action=last_action)

    except Exception as e:
        app.logger.error(f"Exception occurred: {e}", exc_info=True)
        return render_template('interaction.html',
                               form=form,
                               last_action="Error")


@app.route("/call/<interaction_id>", methods=['POST', 'GET'])
@csrf_protect.exempt
def call(interaction_id):
    try:
        recipient_call = Interaction.query.get(session['interaction_id'])
        recipient = Recipient.query.get(recipient_call.recipient_id)
        sender = Sender.query.get(recipient_call.sender_id)

        # Clear the session data now that we're done with it
        if 'interaction_id' in session:
            del session['interaction_id']

        app.logger.info(
            f"Starting call with system prompt '{recipient_call.conversation[0].get('content')}' and user number '{recipient.recipient_phone_number}'"
        )

        # Start a new call
        call = client.calls.create(url=call_webhook_url,
                                   to=recipient.recipient_phone_number,
                                   from_=twilio_number)

        app.logger.info(f"Started call with SID '{call.sid}'")

        #add call.sid to recipient_call
        recipient_call.twilio_conversation_sid = call.sid
        db.session.commit()

        return redirect(
            url_for('interaction',
                    last_action="Calling" + recipient.recipient_name + "for" +
                    sender.sender_name))

    except Exception as e:
        app.logger.error(f"Exception occurred: {e}", exc_info=True)
        return render_template('interaction.html',
                               form=InteractionForm(),
                               last_action="Error")


@app.route("/text_message/<interaction_id>", methods=['POST', 'GET'])
@csrf_protect.exempt
def text_message(interaction_id):
    try:
        text_thread = db.session.query(Interaction).get(interaction_id)

        if text_thread:
            recipient = Recipient.query.get(text_thread.recipient_id)
            conversation = text_thread.conversation

            logging.debug(
                f"Texting route recieved Conversation: {conversation}")

            body = conversation[-1].get('content')

            app.logger.info(
                f"Starting text message with body'{body}' and user number '{recipient.recipient_phone_number}'"
            )

            # Start a new text message thread
            text_message = client.messages.create(
                body=body,
                from_=twilio_number,
                to=recipient.recipient_phone_number)

            logging.info(
                f"Started text Conversation with recipient '{recipient.recipient_name}' on text SID '{text_message.sid}'"
            )

            db.session.commit()

            return jsonify({
                'status': 'success',
                'last_action':
                f"Sending text to {recipient.recipient_name} at {recipient.recipient_phone_number}",
                'First Message': body,
                'conversation': text_thread.conversation
            }), 200

        return jsonify({
            'status':
            'error',
            'last_action':
            f"Error Sending text to with interaction id {interaction_id}"
        }), 400

    except Exception as e:
        app.logger.error(f"Exception occurred: {e}", exc_info=True)
        return render_template('interaction.html',
                               form=InteractionForm(),
                               last_action="Error")


@app.route("/plan/<int:recipient_id>", methods=['GET', 'POST'])
@csrf_protect.exempt
def plan(recipient_id):
    try:
        interaction = Interaction.query.get(session['interaction_id'])
        recipient = interaction.recipient

        most_recent_message = interaction.conversation[-1].get('content')

        logging.info(f"Creating plan for {recipient.recipient_name}")
        logging.debug(f"Conversation so far: {interaction.conversation}")
        logging.info(f"Most Recent Message {most_recent_message}")

        # Instantiate campaign tools
        campaign_tools = CampaignTools(interaction, db)

        # Maximum iterations to avoid infinite loop
        max_iterations = 10
        iteration = 0

        # Execute action based on the recent message
        while True:
            iteration += 1

            if 'Action' in most_recent_message:
                action_name, action_params = extract_action(
                    most_recent_message)
                action_result = execute_action(campaign_tools, action_name,
                                               action_params)
                most_recent_message = f"Observation: {action_result}"
                add_message_to_conversation(interaction, most_recent_message)

            most_recent_message = add_llm_response_to_conversation(interaction)

            # Update conversation with the latest response
            add_message_to_conversation(interaction, most_recent_message)

            # flush the logs
            for handler in logging.getLogger().handlers:
                handler.flush()

            if ('WAIT' in most_recent_message.upper()) or (iteration >=
                                                           max_iterations):
                if iteration >= max_iterations:
                    most_recent_message = "Observation: The conversation exceeded the maximum number of iterations without reaching a 'WAIT' state. The conversation will be paused here, and will need to be reviewed."
                    add_message_to_conversation(interaction,
                                                most_recent_message)
                break

        db.session.commit()
        return jsonify({
            'status': 'success',
            'last_action': 'Planning for ' + recipient.recipient_name,
            'conversation': interaction.conversation
        }), 200

    except Exception as e:
        app.logger.error(f"Exception occurred: {e}", exc_info=True)
        return jsonify({'status': 'error', 'last_action': 'Error'}), 500


#Run the app on port 5000
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
    scheduler.start()

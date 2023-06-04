# import Flask and other libraries
from flask import Response, render_template, request, redirect, url_for, session, jsonify
from twilio.twiml.voice_response import VoiceResponse
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
import os
import openai
from forms.voter_communication_form import VoterCommunicationForm
from models import Voter, Candidate, Race, VoterCommunication
from prompts.campaign_volunteer_agent import get_campaign_phone_call_system_prompt, get_campaign_text_message_system_prompt
from prompts.campaign_planner_agent import get_campaign_agent_system_prompt
from tools.campaign_agent_tools import CampaignTools, extract_action, execute_action
from tools.utility import add_message_to_conversation, add_llm_response_to_conversation, initialize_conversation
from tools.scheduler import scheduler
from logs.logger import logger, logging
from datetime import date
from database import db
from flask_migrate import Migrate
from context import app, csrf_protect

# assuming app and db are defined above
migrate = Migrate(app, db)

# Your Twilio account credentials
account_sid = os.environ['twilio_account_sid']
auth_token = os.environ['twilio_auth_token']
twilio_number = os.environ['twilio_number']

# The webhook URL for handling the call events
call_webhook_url = os.environ['CALL_WEBHOOK_URL']

# Create a Twilio client object
client = Client(account_sid, auth_token)

# set OpenAi Key for GPT4
openai.api_key = os.environ['OPENAI_API_KEY_GPT4']


# Define a route for handling Twilio webhook requests
@app.route("/twilio_call", methods=['GET', 'POST'])
@csrf_protect.exempt
def twilio_call():
    try:
        logging.info("Twilio Phone Call Request Received")
        logging.info(request.get_data())
        call_id = request.form['CallSid']
        logging.info("Call id: " + call_id)
        voter_communication = VoterCommunication.query.filter_by(
            twilio_conversation_sid=call_id).first()

        # Retrieve the conversation from our 'database' using the CallSid
        conversation = voter_communication.conversation

        # If conversation does not exist, log an error and return
        if not conversation:
            logging.error('Could not retrieve conversation from database.')
            return Response('Failed to retrieve conversation.', status=500)

        # Retrieve the speech result from the Twilio request
        speech_result = request.values.get('SpeechResult', None)

        response = VoiceResponse()

        # Add the user's message to the conversation
        if speech_result:
            add_message_to_conversation(voter_communication, speech_result)
            # Log the user's message to the console
            logger.info(f"User message: {speech_result}")

            # Get the AI response and add it to the conversation
            try:
                text = add_llm_response_to_conversation(voter_communication)
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

    # Use the 'From' number to look up the voter in your database
    voter = Voter.query.filter_by(voter_phone_number=from_number).first()

    # If the voter doesn't exist, create a new one and a new VoterCommunication
    if not voter:
        voter = Voter(voter_name='', voter_phone_number=from_number)
        db.session.add(voter)

        system_prompt = get_campaign_text_message_system_prompt(
            voter, Candidate(),
            Race(race_date=date.tomorrow(),
                 race_name="Next Congressional Race Example",
                 race_information="Important upcoming race tomorrow"))

        # Create a new conversation with a system message
        conversation = initialize_conversation(system_prompt)

        voter_communication = VoterCommunication(twilio_conversation_sid='',
                                                 conversation=conversation,
                                                 communication_type='text',
                                                 voter_id=voter.id)
        db.session.add(voter_communication)
    else:
        # If the voter exists, find the VoterCommunication for this voter with type 'text'
        voter_communication = VoterCommunication.query.filter_by(
            voter_id=voter.id, communication_type='text').first()

    # Now you can add the new message to the conversation
    message_body = request.values.get('Body', None)
    logging.info(f"Recieved message body: {message_body}")
    voter_communication.conversation = add_message_to_conversation(
        voter_communication, message_body)

    logging.info(
        f"Conversation after including message: {voter_communication.conversation}"
    )
    # generate a new response from openAI to continue the conversation
    message_body = add_llm_response_to_conversation(voter_communication)
    logging.debug(f"AI message: {message_body}")
    logging.info(
        f"Conversation after adding LLM response: {voter_communication.conversation}"
    )

    db.session.add(voter_communication)
    db.session.commit()

    response = MessagingResponse()
    response.message(message_body)
    logging.debug(f"Response xml: {response.to_xml()}")
    return Response(response.to_xml(), content_type="text/xml")


@app.route("/", methods=['GET', 'POST'])
def home():
    return redirect(
        url_for('voter_communication',
                last_action="LoadingServerForTheFirstTime"))


@app.route('/voter_communication/<last_action>', methods=['GET', 'POST'])
@csrf_protect.exempt
def voter_communication(last_action):
    try:
        app.logger.info("Processing voter communication form...")

        # Create instance of VoterCallForm class
        form = VoterCommunicationForm()

        # When the form is submitted
        if form.validate_on_submit():
            # Check if a voter with the given name and phone number already exists
            voter = Voter.query.filter_by(
                voter_name=form.voter_name.data,
                voter_phone_number=form.voter_phone_number.data).first()

            # If the voter does not exist, create a new one
            if not voter:
                voter = Voter(voter_name=form.voter_name.data,
                              voter_phone_number=form.voter_phone_number.data,
                              voter_information=form.voter_information.data)
                db.session.add(voter)

            # Check if candidate with this name is in database
            candidate = Candidate.query.filter_by(
                candidate_name=form.candidate_name.data).first()

            if not candidate:
                candidate = Candidate(
                    candidate_name=form.candidate_name.data,
                    candidate_information=form.candidate_information.data)
                db.session.add(candidate)

            # Check if race wiht this name is in database
            race = Race.query.filter_by(race_name=form.race_name.data).first()

            if not race:
                race = Race(race_name=form.race_name.data,
                            race_information=form.race_information.data)
                db.session.add(race)

            communication_type = form.communication_type.data

            # Create the VoterCommunication
            voter_communication = VoterCommunication(
                twilio_conversation_sid='',  # You will need to update this later
                conversation=[],
                voter=voter,  # The ID of the voter
                candidate=candidate,
                race=race,
                communication_type=communication_type)

            db.session.add(voter_communication)
            db.session.commit()

            #get communication with DB fields
            voter_communication = db.session.query(
                VoterCommunication).filter_by(
                    voter_id=voter.id,
                    communication_type=communication_type).first()

            if communication_type == "call":
                # Add information from VoterCallForm to the system prompt
                system_prompt = get_campaign_phone_call_system_prompt(
                    voter_communication)
            elif communication_type == "text":
                system_prompt = get_campaign_text_message_system_prompt(
                    voter_communication)
            elif communication_type == "plan":
                system_prompt = get_campaign_agent_system_prompt(
                    voter_communication)

            user_number = form.voter_phone_number.data

            #Pre create the first response
            conversation = initialize_conversation(system_prompt)
            voter_communication.conversation = conversation
            initial_statement = add_llm_response_to_conversation(
                voter_communication)
            logging.info("Voter communication created successfully")
            db.session.commit()

            # Log the system prompt and user number
            logging.info("Communication Type: %s", communication_type)
            logging.info(f"System prompt: {system_prompt}")
            logging.info(f"User number: {user_number}")
            logging.info(f"Initial Statement: {initial_statement}")
            logging.info(f"Conversation: {conversation}")

            # Store data in session
            session[
                'voter_communication_id'] = voter_communication.id  # Store the VoterCommunication ID

            if (communication_type == "call"):
                # Call the voter
                logging.info("Redirecting to call route...")
                return redirect(url_for('call'))
            elif (communication_type == "text"):
                # Send a text message
                logging.info("Redirecting to text message route...")
                return redirect(
                    url_for('text_message',
                            voter_communication_id=voter_communication.id))
            elif (communication_type == "plan"):
                # Create an outreach agent and plan the outreach for the voter
                logging.info("Redirecting to planning route...")
                return redirect(url_for('plan', voter_id=voter.id))

        return render_template('voter_communication.html',
                               form=form,
                               last_action=last_action)

    except Exception as e:
        app.logger.error(f"Exception occurred: {e}", exc_info=True)
        return render_template('voter_communication.html',
                               form=form,
                               last_action="Error")


@app.route("/call", methods=['POST', 'GET'])
@csrf_protect.exempt
def call():
    try:
        voter_call = VoterCommunication.query.get(
            session['voter_communication_id'])
        voter = Voter.query.get(voter_call.voter_id)
        candidate = Candidate.query.get(voter_call.candidate_id)

        # Clear the session data now that we're done with it
        if 'voter_communication_id' in session:
            del session['voter_communication_id']

        app.logger.info(
            f"Starting call with system prompt '{voter_call.conversation[0].get('content')}' and user number '{voter.voter_phone_number}'"
        )

        # Start a new call
        call = client.calls.create(url=call_webhook_url,
                                   to=voter.voter_phone_number,
                                   from_=twilio_number)

        app.logger.info(f"Started call with SID '{call.sid}'")

        #add call.sid to voter_call
        voter_call.twilio_conversation_sid = call.sid
        db.session.commit()

        return redirect(
            url_for('voter_communication',
                    last_action="Calling" + voter.voter_name + "for" +
                    candidate.candidate_name))

    except Exception as e:
        app.logger.error(f"Exception occurred: {e}", exc_info=True)
        return render_template('voter_communication.html',
                               form=VoterCommunicationForm(),
                               last_action="Error")


@app.route("/text_message/<voter_communication_id>", methods=['POST', 'GET'])
@csrf_protect.exempt
def text_message(voter_communication_id):
    try:
        voter_text_thread = db.session.query(VoterCommunication).get(
            voter_communication_id)

        if voter_text_thread:
            voter = Voter.query.get(voter_text_thread.voter_id)
            conversation = voter_text_thread.conversation

            logging.info(
                f"Texting route recieved Conversation: {conversation}")

            body = conversation[-1].get('content')

            # Clear the session data now that we're done with it
            if 'voter_communication_id' in session:
                del session['voter_communication_id']

            app.logger.info(
                f"Starting text message with body'{body}' and user number '{voter.voter_phone_number}'"
            )

            # Start a new text message thread
            text_message = client.messages.create(body=body,
                                                  from_=twilio_number,
                                                  to=voter.voter_phone_number)

            logging.info(
                f"Started text Conversation with voter '{voter.voter_name}' on text SID '{text_message.sid}'"
            )

            db.session.commit()

            return jsonify({
                'status': 'success',
                'last_action':
                f"Sending text to {voter.voter_name} at {voter.voter_phone_number}",
                'First Message': body,
                'conversation': voter_text_thread.conversation
            }), 200

        return jsonify({
            'status':
            'error',
            'last_action':
            f"Error Sending text to with communication id {voter_communication_id}"
        }), 400

    except Exception as e:
        app.logger.error(f"Exception occurred: {e}", exc_info=True)
        return render_template('voter_communication.html',
                               form=VoterCommunicationForm(),
                               last_action="Error")


@app.route("/plan/<int:voter_id>", methods=['GET', 'POST'])
@csrf_protect.exempt
def plan(voter_id):
    try:
        voter_communication = VoterCommunication.query.get(
            session['voter_communication_id'])
        voter = voter_communication.voter

        most_recent_message = voter_communication.conversation[-1].get(
            'content')

        logging.info(f"Creating plan for {voter.voter_name}")
        logging.debug(
            f"Conversation so far: {voter_communication.conversation}")
        logging.info(f"Most Recent Message {most_recent_message}")

        # Instantiate campaign tools
        campaign_tools = CampaignTools(voter_communication, db)

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
                add_message_to_conversation(voter_communication,
                                            most_recent_message)

            most_recent_message = add_llm_response_to_conversation(
                voter_communication)

            # Update conversation with the latest response
            add_message_to_conversation(voter_communication,
                                        most_recent_message)

            # flush the logs
            for handler in logging.getLogger().handlers:
                handler.flush()

            if ('WAIT' in most_recent_message.upper()) or (iteration >=
                                                           max_iterations):
                if iteration >= max_iterations:
                    most_recent_message = "Observation: The conversation exceeded the maximum number of iterations without reaching a 'WAIT' state. The conversation will be paused here, and will need to be reviewed."
                    add_message_to_conversation(voter_communication,
                                                most_recent_message)
                break

        db.session.commit()
        return jsonify({
            'status': 'success',
            'last_action': 'Planning for ' + voter.voter_name,
            'conversation': voter_communication.conversation
        }), 200

    except Exception as e:
        app.logger.error(f"Exception occurred: {e}", exc_info=True)
        return jsonify({'status': 'error', 'last_action': 'Error'}), 500


#Run the app on port 5000
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
    scheduler.start()

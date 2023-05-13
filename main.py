# import Flask and other libraries
from flask import Flask, Response, render_template, request, redirect, url_for, session
from flask_wtf.csrf import CSRFProtect
from twilio.twiml.voice_response import VoiceResponse
import os
# Import the Twilio and Eleven Labs libraries
from twilio.rest import Client
import openai
from forms.voter_call_form import VoterCallForm
from models import Voter, Candidate, Race, VoterCall, db
from prompts.campaign_assistant_agent import get_campaign_assistant_system_prompt
import secrets
import logging

# Create a logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)  # Set the logging level

# Create a file handler
file_handler = logging.FileHandler('logs/twilio.log')
file_handler.setLevel(logging.INFO)  # Set the logging level for the file

# Create a console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)  # Set the logging level for the console

# Create a formatter and set it for both handlers
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add the handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Create a Flask app object
app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(nbytes=8)
csrf_protect = CSRFProtect(app)
# Set the SQLALCHEMY_DATABASE_URI configuration variable
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db.init_app(app)

# Your Twilio account credentials
account_sid = os.environ['twilio_account_sid']
auth_token = os.environ['twilio_auth_token']
twilio_number = os.environ['twilio_number']

# The webhook URL for handling the call events
webhook_url = "http://ai-phone-bank-poc.a1j9o94.repl.co/twilio"

# Create a Twilio client object
client = Client(account_sid, auth_token)

# set OpenAi Key for GPT4
openai.api_key = os.environ['OPENAI_API_KEY_GPT4']


# Define a route for handling Twilio webhook requests
@app.route("/twilio", methods=['POST'])
@csrf_protect.exempt
def twilio():
    try:
        call_id = request.form['CallSid']
        logging.info("Twilio incoming call received for Call id: " + call_id)
        voter_call = VoterCall.query.filter_by(twilio_call_sid=call_id).first()

        # Retrieve the conversation from our 'database' using the CallSid
        conversation = voter_call.conversation

        # If conversation does not exist, log an error and return
        if not conversation:
            logging.error('Could not retrieve conversation from database.')
            return Response('Failed to retrieve conversation.', status=500)

        # Retrieve the speech result from the Twilio request
        speech_result = request.values.get('SpeechResult', None)

        response = VoiceResponse()

        # Add the user's message to the conversation
        if speech_result:
            conversation.append({"role": "user", "content": speech_result})
            # Log the user's message to the console
            logger.info(f"User message: {speech_result}")

        # Get the AI response and add it to the conversation
        try:
            completion = openai.ChatCompletion.create(model="gpt-3.5-turbo",
                                                      messages=conversation,
                                                      temperature=0.3)

            text = completion.choices[0].message.content
        except:
            text = "Sorry, I am having trouble hearing you. I will try to call again later, Goodbye"
        conversation.append({"role": "assistant", "content": text})
        logger.info(f"AI message: {text}")

        # Return the response as XML
        response.say(text, voice='Polly.Joanna-Neural')

        #check if text contains "goodbye", if so, hang up the call, other wise continue gathering input
        if "goodbye" in text.lower():
            response.hangup()
            logging.info("Goodbye message received, hanging up call")
        else:
            response.gather(input="speech",
                            action=webhook_url,
                            method="POST",
                            speech_model='experimental_conversations')
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


@app.route("/", methods=['GET', 'POST'])
def home():
    return redirect(
        url_for('voter_call', last_action="LoadingServerForTheFirstTime"))


@app.route('/voter_call/<last_action>', methods=['GET', 'POST'])
@csrf_protect.exempt
def voter_call(last_action):
    try:
        app.logger.info("Processing voter call...")

        # Create instance of VoterCallForm class
        form = VoterCallForm()

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
                db.session.commit()

            # Check if candidate with this name is in database
            candidate = Candidate.query.filter_by(
                candidate_name=form.candidate_name.data).first()

            if not candidate:
                candidate = Candidate(
                    candidate_name=form.candidate_name.data,
                    candidate_information=form.candidate_information.data)
                db.session.add(candidate)
                db.session.commit()

            # Check if race wiht this name is in database
            race = Race.query.filter_by(race_name=form.race_name.data).first()

            if not race:
                race = Race(race_name=form.race_name.data,
                            race_information=form.race_information.data)
                db.session.add(race)
                db.session.commit()

            # Add information from VoterCallForm to the system prompt
            system_prompt = get_campaign_assistant_system_prompt(
                form.voter_name.data, form.race_name.data, form.race_date.data,
                form.candidate_name.data, form.race_information.data,
                form.candidate_information.data, form.voter_information.data)
            user_number = form.voter_phone_number.data

            # Create the VoterCall
            voter_call = VoterCall(
                twilio_call_sid='',  # You will need to update this later
                conversation=[{
                    "role": "system",
                    "content": system_prompt
                }],
                voter_id=voter.id,  # The ID of the voter
                candidate_id=candidate.id,
                race_id=race.id)
            db.session.add(voter_call)
            db.session.commit()
            logging.info("Voter call created successfully")

            # Log the system prompt and user number
            app.logger.info(f"System prompt: {system_prompt}")
            app.logger.info(f"User number: {user_number}")

            # Store data in session
            session['voter_call_id'] = voter_call.id  # Store the VoterCall ID

            app.logger.info("Redirecting to call route...")
            return redirect(url_for('call'))

        return render_template('voter_call.html',
                               form=form,
                               last_action=last_action)

    except Exception as e:
        app.logger.error(f"Exception occurred: {e}", exc_info=True)
        return render_template('voter_call.html',
                               form=form,
                               last_action="Error")


@app.route("/call", methods=['POST', 'GET'])
@csrf_protect.exempt
def call():
    try:
        voter_call = VoterCall.query.get(session['voter_call_id'])
        voter = Voter.query.get(voter_call.voter_id)
        candidate = Candidate.query.get(voter_call.candidate_id)

        # Clear the session data now that we're done with it
        if 'voter_call_id' in session:
            del session['voter_call_id']

        app.logger.info(
            f"Starting call with system prompt '{voter_call.conversation[0].get('content')}' and user number '{voter.voter_phone_number}'"
        )

        # Start a new call
        call = client.calls.create(url=webhook_url,
                                   to=voter.voter_phone_number,
                                   from_=twilio_number)

        app.logger.info(f"Started call with SID '{call.sid}'")

        #add call.sid to voter_call
        voter_call.twilio_call_sid = call.sid
        db.session.commit()

        return redirect(
            url_for('voter_call',
                    last_action="Calling" + voter.voter_name + "for" +
                    candidate.candidate_name))

    except Exception as e:
        app.logger.error(f"Exception occurred: {e}", exc_info=True)
        return render_template('voter_call.html',
                               form=VoterCallForm(),
                               last_action="Error")


#Run the app on port 5000
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)

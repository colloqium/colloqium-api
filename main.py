# import Flask and other libraries
from flask import Flask, Response, render_template, request, redirect, url_for, session
from flask_wtf.csrf import CSRFProtect
from twilio.twiml.voice_response import VoiceResponse
import os
# Import the Twilio and Eleven Labs libraries
from twilio.rest import Client
import openai
from forms.voter_call_form import VoterCallForm
from prompts.campaign_assistant_agent import get_campaign_assistant_system_prompt
import secrets
import logging

# Create a logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)  # Set the logging level

# Create a file handler
file_handler = logging.FileHandler('twilio.log')
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

# Your Twilio account credentials
account_sid = os.environ['twilio_account_sid']
auth_token = os.environ['twilio_auth_token']
twilio_number = os.environ['twilio_number']

# The webhook URL for handling the call events
webhook_url = "http://ai-phone-bank-poc.a1j9o94.repl.co/twilio"

# Create a Twilio client object
client = Client(account_sid, auth_token)

# A simple dictionary to represent our database - replace with your real database
db = {}


# Define a route for handling Twilio webhook requests
@app.route("/twilio", methods=['POST'])
@csrf_protect.exempt
def twilio():
    try:
        # Set up logging
        logging.basicConfig(filename='twilio.log', level=logging.INFO)

        # Retrieve the conversation from our 'database' using the CallSid
        conversation = db.get(request.values.get('CallSid', ''))

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

        # Get the AI response and add it to the conversation
        completion = openai.ChatCompletion.create(model="gpt-3.5-turbo",
                                                  messages=conversation,
                                                  temperature=0.7)

        text = completion.choices[0].message.content
        conversation.append({"role": "assistant", "content": text})

        # Update the conversation in our 'database'
        db[request.values.get('CallSid', '')] = conversation

        # Return the response as XML
        response.say(text)
        response.gather(input="speech", action=webhook_url, method="POST")

        response_xml = response.to_xml()

        logging.info('Response successfully created and returned.')
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
    return redirect(url_for('voter_call'))


@app.route('/voter_call', methods=['GET', 'POST'])
@csrf_protect.exempt
def voter_call():
    try:
        app.logger.info("Processing voter call...")

        # Create instance of VoterCallForm class
        form = VoterCallForm()

        # When the form is submitted
        if form.validate_on_submit():
            # Add information from VoterCallForm to the system prompt
            # Update system prompt with form data
            system_prompt = get_campaign_assistant_system_prompt(
                form.voter_name.data, form.race_name.data, form.race_date.data,
                form.candidate_name.data, form.race_information.data,
                form.candidate_information.data, form.voter_information.data)
            user_number = form.voter_phone_number.data

            # Log the system prompt and user number
            app.logger.info(f"System prompt: {system_prompt}")
            app.logger.info(f"User number: {user_number}")

            # Store data in session
            session['system_prompt'] = system_prompt
            session['user_number'] = user_number

            app.logger.info("Redirecting to call route...")
            return redirect(url_for('call'))

        return render_template('voter_call.html', form=form)

    except Exception as e:
        app.logger.error(f"Exception occurred: {e}", exc_info=True)
        return render_template('voter_call.html', form=form)


@app.route("/call", methods=['POST', 'GET'])
@csrf_protect.exempt
def call():
    try:
        # Retrieve data from session
        system_prompt = session.get('system_prompt', '')
        user_number = session.get('user_number', '')

        # Clear the session data now that we're done with it
        if 'system_prompt' in session:
            del session['system_prompt']
        if 'user_number' in session:
            del session['user_number']

        app.logger.info(
            f"Starting call with system prompt '{system_prompt}' and user number '{user_number}'"
        )

        # Start a new call
        call = client.calls.create(url=webhook_url,
                                   to=user_number,
                                   from_=twilio_number)

        app.logger.info(f"Started call with SID '{call.sid}'")

        # Create the initial conversation with the system message
        conversation = [{"role": "system", "content": system_prompt}]

        # Store the conversation in our 'database' keyed by the call SID
        db[call.sid] = conversation

        # Return a TwiML response
        return redirect(url_for('voter_call'))

    except Exception as e:
        app.logger.error(f"Exception occurred: {e}", exc_info=True)


#Run the app on port 5000
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)

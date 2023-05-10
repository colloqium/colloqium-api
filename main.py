# import Flask and other libraries
from flask import Flask, Response, render_template, request
from twilio.twiml.voice_response import VoiceResponse
import os
# Import the Twilio and Eleven Labs libraries
from twilio.rest import Client
import openai

# Create a Flask app object
app = Flask(__name__)

# Your Twilio account credentials
account_sid = os.environ['twilio_account_sid']
auth_token = os.environ['twilio_auth_token']
twilio_number = os.environ['twilio_number']

# The user's phone number
user_number = "+17066641258"

# The webhook URL for handling the call events
webhook_url = "http://ai-phone-bank-poc.a1j9o94.repl.co/twilio"

# Create a Twilio client object
client = Client(account_sid, auth_token)

# GPT API System Prompts
system_prompt = "You are a campaign worker trying to convince someone to go vote, and vote for your preferred candidate. You speak casually, and try not to overwhelm people with information. You're responses should be concicse, informative, and understanding. You ask lots of questions to understand what is important to each voter. Begin by asking the voter if they are aware of the up coming election. Do not reveal that you are an AI bot."

conversation = [{"role": "system", "content": system_prompt}]


# Define a route for handling Twilio webhook requests
@app.route("/twilio", methods=['POST'])
def twilio():
	"""Check if the request has a gather response. If it does, then gather the speech, get the response from the AI, and send it back to the user.""" ""
	# Parse the Twilio request
	speech_result = request.values.get('SpeechResult', None)
	response = VoiceResponse()

	if speech_result:
		# Parse the gather response
		print(speech_result)
		user_response = {"role": "user", "content": speech_result}
		conversation.append(user_response)
		completion = openai.ChatCompletion.create(model="gpt-3.5-turbo",
		                                          messages=conversation,
		                                          temperature=0.7)

	else:
		completion = openai.ChatCompletion.create(model="gpt-3.5-turbo",
		                                          messages=conversation,
		                                          temperature=0.7)
	text = completion.choices[0].message.content
	conversation.append(completion.choices[0].message)
	# Return the response as XML
	response.say(text)
	response.gather(input="speech", action=webhook_url, method="POST")
	print(response.to_xml())
	return Response(response.to_xml(), content_type="text/xml")


@app.route("/", methods=['GET', 'POST'])
def home():
	return render_template('home.html')


@app.route("/call", methods=['POST'])
def call():
	# Start a new call
	call = client.calls.create(url=webhook_url,
	                           to=user_number,
	                           from_=twilio_number)
	print(call)

	# Return a TwiML response
	return render_template('home.html', result="Made Call")


#Run the app on port 5000
if __name__ == "__main__":
	app.run(host='0.0.0.0', port=5000)

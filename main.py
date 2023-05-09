# import Flask and other libraries
from flask import Flask, Response
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
webhook_url = "https://ai-phone-bank-poc.a1j9o94.repl.co/twilio"

# Create a Twilio client object
client = Client(account_sid, auth_token)


# Define a route for handling Twilio webhook requests
@app.route("/twilio", methods=['POST'])
def twilio():
	response = VoiceResponse()
	completion = openai.ChatCompletion.create(
	 model="gpt-3.5-turbo",
	 messages=[
	  {
	   "role":
	   "system",
	   "content":
	   "You are a campaign worker trying to convince someone to go vote, and vote for your preferred candidate."
	  },
	 ],
	 temperature=0.7)
	text = completion.choices[0].message.content
	response.say(text)
	response.say(completion.choices[0].message.content)
	# Return the response as XML
	print(response.to_xml())
	return Response(response.to_xml(), content_type="text/xml")


#Run the app on port 5000
if __name__ == "__main__":
	app.run(host='0.0.0.0', port=5000)

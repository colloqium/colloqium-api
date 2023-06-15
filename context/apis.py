from twilio.rest import Client
import os
import openai
from dotenv import load_dotenv

load_dotenv()
# Your Twilio account credentials
account_sid = os.environ['twilio_account_sid']
auth_token = os.environ['twilio_auth_token']
twilio_number = os.environ['twilio_number']

# The webhook URL for handling the call events
call_webhook_url = f"{os.environ['BASE_URL']}/twilio_call"

# Create a Twilio client object
client = Client(account_sid, auth_token)

# set OpenAi Key for GPT4
openai.api_key = os.environ['OPENAI_API_KEY']
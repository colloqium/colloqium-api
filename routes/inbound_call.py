from flask import Blueprint
# import Flask and other libraries
from flask import Response, request
from twilio.twiml.voice_response import VoiceResponse
from models.models import Interaction
from tools.utility import add_message_to_conversation, add_llm_response_to_conversation
# from logs.logger import logger, logging
from context.database import db
from context.apis import call_webhook_url


inbound_call_bp = Blueprint('inbound_call', __name__)

# Define a route for handling Twilio webhook requests
@inbound_call_bp.route("/inbound_call", methods=['POST'])
def inbound_call():
    try:
        print("Twilio Phone Call Request Received")
        print(request.get_data())
        call_id = request.form['CallSid']
        print("Call id: " + call_id)
        interaction = Interaction.query.filter_by(
            twilio_conversation_sid=call_id).first()

        # Retrieve the conversation from our 'database' using the CallSid
        conversation = interaction.conversation

        # If conversation does not exist, log an error and return
        if not conversation:
            print('Could not retrieve conversation from database.')
            return Response('Failed to retrieve conversation.', status=500)

        # Retrieve the speech result from the Twilio request
        speech_result = request.values.get('SpeechResult', None)

        response = VoiceResponse()

        # Add the user's message to the conversation
        if speech_result:
            add_message_to_conversation(interaction, speech_result)
            # Log the user's message to the console
            print(f"User message: {speech_result}")

            # Get the AI response and add it to the conversation
            try:
                text = add_llm_response_to_conversation(interaction)
            except:
                text = "Sorry, I am having trouble hearing you. I will try to call again later, Goodbye"
            conversation.append({"role": "assistant", "content": text})
        else:
            # This is the first message and you can just use the completion
            text = conversation[-1]['content']

        print(f"AI message: {text}")

        # Return the response as XML
        response.say(text)

        #check if text contains "goodbye", if so, hang up the call, other wise continue gathering input
        if "goodbye" in text.lower():
            response.hangup()
            print("Goodbye message received, hanging up call")
        else:
            response.gather(input="speech",
                            action=call_webhook_url,
                            method="POST")
            print("Gathering input from user")

        response_xml = response.to_xml()

        print('Response successfully created and returned.')
        db.session.commit()
        return Response(response_xml, content_type="text/xml")

    except Exception as e:
        # Log the exception
        print('An error occurred while processing the request: %s',
                          e)
        # Return a server error response
        return Response('An error occurred while processing the request.',
                        status=500)
from flask import Blueprint, request
# import Flask and other libraries
from flask import jsonify
from models.models import Recipient, Interaction, Sender, InteractionStatus
# from logs.logger import logger, logging
from context.database import db
from context.apis import client
from tools.utility import format_phone_number
from context.analytics import analytics, EVENT_OPTIONS
from context.apis import base_url

send_text_bp = Blueprint('send_text', __name__)


@send_text_bp.route("/send_text/", methods=['POST'])
def send_text():
    
    #check if the request includes the required confirmations

    request_erros = get_request_errors(request)
    if len(request_erros) > 0:
        print("missing required fields  in request")
        return jsonify({'status': 'error', 'last_action': 'missing_required_fields', 'errors': request_erros})
    
    interaction_id = request.json.get('interaction_id')

    try:
        text_thread = db.session.query(Interaction).get(interaction_id)
        #set the interaction_status to InteractionStatus.HUMAN_CONFIRMED
        text_thread.interaction_status = InteractionStatus.HUMAN_CONFIRMED

        if text_thread:
            recipient = Recipient.query.get(text_thread.recipient_id)
            sender = Sender.query.get(text_thread.sender_id)
            conversation = text_thread.conversation

            print(
                f"Texting route recieved Conversation: {conversation}")

            body = conversation[-1].get('content')

            print(
                f"Starting text message with body'{body}' and user number '{recipient.recipient_phone_number}'"
            )

            callback_route = base_url + "twilio_message_callback"
            print(f"Sending callback to '{callback_route}'")

            # Start a new text message thread
            text_message = client.messages.create(
                body=body,
                from_=sender.sender_phone_number,
                to=format_phone_number(recipient.recipient_phone_number),
                status_callback=callback_route)

            print(
                f"Started text Conversation with recipient '{recipient.recipient_name}' on text SID '{text_message.sid}'"
            )
            analytics.track(recipient.id, EVENT_OPTIONS.sent, {
                'interaction_id': interaction_id,
                'interaction_type': text_thread.interaction_type,
                'recipient_name': recipient.recipient_name,
                'recipient_phone_number': recipient.recipient_phone_number,
                'sender_name': sender.sender_name,
                'sender_phone_number': sender.sender_phone_number,
                'message': body,
            })

            db.session.commit()

            return jsonify({
                'status': 'success',
                'last_action':
                f"Sending text to {recipient.recipient_name} at {recipient.recipient_phone_number}",
                'First Message': body,
                'conversation': text_thread.conversation
            }), 200
        else:
            print(f"No interaction found with id {interaction_id}")

        return jsonify({
            'status':
            'error',
            'last_action':
            f"Error Sending text to with interaction id {interaction_id}"
        }), 400

    except Exception as e:
        print(f"Exception occurred: {e}", exc_info=True)
        return jsonify({
            'status':
            'error',
            'last_action':
            f"Error Sending text. Exception: {e}"
        }), 400
    


#Returns none or returns an array of error messages
def get_request_errors(request):
    
    errors = []

    
    #check if the request has a json body
    if not request.json:
        errors.append("No json body in request")

    #check if there is an interaction_status field
    if not 'interaction_status' in request.json:
        errors.append("No interaction_status field in request")


    #check if the interaction_status is InteractionStatus.HUMAN_CONFIRMED
    if not request.json.get('interaction_status') == InteractionStatus.HUMAN_CONFIRMED:
        errors.append("interaction_status is not InteractionStatus.HUMAN_CONFIRMED")
    
    #check if the request has an "interaction_id" field
    if not 'interaction_id' in request.json:
        errors.append("No interaction_id field in request")
    
    return errors
from flask import Blueprint, request, Response
# import Flask and other libraries
from flask import jsonify
from models.sender import Sender
from models.interaction import Interaction, InteractionStatus
from models.voter import Voter
from context.database import db
from context.apis import client
from tools.utility import format_phone_number
from context.analytics import analytics, EVENT_OPTIONS
from context.apis import twilio_messaging_service_sid, message_webhook_url
from twilio.twiml.messaging_response import MessagingResponse

send_text_bp = Blueprint('send_text', __name__)


@send_text_bp.route("/send_text", methods=['POST', 'OPTIONS'])
def send_text():
    print("send_text route called")

    if request.method == 'OPTIONS':
        print("OPTIONS request")
        # Preflight request. Reply successfully:
        resp = Response(status=200)
        resp.headers['Access-Control-Allow-Origin'] = '*'
        resp.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        resp.headers['Access-Control-Allow-Headers'] = 'content-type'
        return resp
    
    #check if the request includes the required confirmations

    request_errors = get_request_errors(request)
    if len(request_errors) > 0:
        print("missing required fields  in request")
        print(f"Errors: , {request_errors}")
        return jsonify({'status': 'error', 'last_action': 'missing_required_fields', 'errors': request_errors})
    
    interaction_id = request.json.get('interaction_id')


    response = Response(str(MessagingResponse()), mimetype='application/xml')

    try:
        text_thread = db.session.query(Interaction).get(interaction_id)
        
        #set the interaction_status to InteractionStatus.HUMAN_CONFIRMED
        text_thread.interaction_status = InteractionStatus.HUMAN_CONFIRMED

        if text_thread:
            voter = Voter.query.get(text_thread.voter_id)
            sender = Sender.query.get(text_thread.sender_id)
            conversation = text_thread.conversation

            # print( f"Texting route recieved Conversation: {conversation}")

            # Depends on the fact that this is the first message in the conversation. Should move to a more robust solution
            body = conversation[-1].get('content')

            # print(f"Starting text message with body'{body}' and user number '{voter.voter_phone_number}'")


            sender_phone_number = sender.phone_numbers[0].get_full_phone_number()
            
            # Start a new text message thread
            client.messages.create(
                body=body,
                from_=format_phone_number(sender_phone_number),
                to=format_phone_number(voter.voter_phone_number),
                status_callback=message_webhook_url,
                messaging_service_sid=twilio_messaging_service_sid)

            # print(f"Started text Conversation with voter '{voter.voter_name}' on text SID '{text_message.sid}'")
            analytics.track(voter.id, EVENT_OPTIONS.sent, {
                'interaction_id': interaction_id,
                'interaction_type': text_thread.interaction_type,
                'voter_name': voter.voter_name,
                'voter_phone_number': voter.voter_phone_number,
                'sender_name': sender.sender_name,
                'sender_phone_number': sender_phone_number,
                'message': body,
            })

            text_thread.interaction_status = InteractionStatus.SENT

            db.session.add(text_thread)
            db.session.commit()

            return response, 200
        else:
            return response, 400

    except Exception as e:
        response, 400
    


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
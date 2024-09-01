from flask import Blueprint, request, Response
# import Flask and other libraries
from flask import jsonify
from models.interaction import Interaction, InteractionStatus, SenderVoterRelationship
from context.database import db
from twilio.twiml.messaging_response import MessagingResponse
from tasks.send_message import send_message

send_text_bp = Blueprint('send_text', __name__)

"""Route to send text messages. Requires a json body with the following fields:
interaction_status: InteractionStatus.HUMAN_CONFIRMED
interaction_id: the id of the interaction to send a text message for

The message needs to have been generated before this is called. This route will not generate a message.
TODO: Check if the message has been generated before sending it

Keyword arguments:
argument -- description
Return: return_description
"""

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
        print("Inside try block")
        text_thread = db.session.query(Interaction).get(interaction_id)
        
        #set the interaction_status to InteractionStatus.HUMAN_CONFIRMED
        text_thread.interaction_status = InteractionStatus.HUMAN_CONFIRMED

        if text_thread:

            print("text_thread found")
            # get the planner for this message
            # tell the planner that the message has been human confirmed and is ready to be sent

            relationship = SenderVoterRelationship.query.filter_by(voter_id=text_thread.voter_id, sender_id=text_thread.sender_id).first()
            # filter the relationship.agents for an agent with the name planning_agent

            #if no relationship, return an error
            if not relationship:
                print("No relationship found for this interaction")
                return jsonify({'status': 'error', 'last_action': 'send_text', 'errors': ["No relationship found for this interaction"]})
            
            print("relationship found")



            print(f"relationship.agents: {relationship.agents}")
            body = text_thread.conversation[-1].get('content')

            sender_phone_number = text_thread.select_phone_number()

            send_message.apply_async(args=[body, sender_phone_number, text_thread.voter_id, text_thread.sender.id, text_thread.id])
            return jsonify({'status': 'success', 'last_action': 'send_text'}), 200
        else:
            return jsonify({'status': 'error', 'last_action': 'send_text', 'errors': ['Text thread not found']}), 400

    except Exception as e:
        print(f"Exception: {e}")
        # add the error to the response
        return jsonify({'status': 'error', 'last_action': 'send_text', 'errors': [str(e)]})
    


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
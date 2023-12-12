from flask import Blueprint, request, Response
# import Flask and other libraries
from flask import jsonify
from models.interaction import Interaction, InteractionStatus, SenderVoterRelationship
from context.database import db
from twilio.twiml.voice_response import VoiceResponse
from tasks.make_robo_call import make_robo_call_task
from logs.logger import logger

make_robo_call_bp = Blueprint('make_robo_call', __name__)

"""Route to make robo_calls. Requires a json body with the following fields:
interaction_status: InteractionStatus.HUMAN_CONFIRMED
interaction_id: the id of the interaction to mak the robo call for

The script needs to have been generated before this is called. This route will not generate a script.
TODO: Check if the message has been generated before sending it

Keyword arguments:
argument -- description
Return: return_description
"""

@make_robo_call_bp.route("/make_robo_call", methods=['POST', 'OPTIONS'])
def make_robo_call():
    print("make_robo_call route called")

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


    response = Response(str(VoiceResponse()), mimetype='application/xml')

    try:
        print("Inside try block")
        call_thread = db.session.query(Interaction).get(interaction_id)
        
        #set the interaction_status to InteractionStatus.HUMAN_CONFIRMED
        call_thread.interaction_status = InteractionStatus.HUMAN_CONFIRMED

        if call_thread:

            print("call_thread found")
            # get the planner for this call
            # tell the planner that the call has been human confirmed and has been made

            relationship = SenderVoterRelationship.query.filter_by(voter_id=call_thread.voter_id, sender_id=call_thread.sender_id).first()

            #if no relationship, return an error
            if not relationship:
                print("No relationship found for this interaction")
                return jsonify({'status': 'error', 'last_action': 'make_robo_call', 'errors': ["No relationship found for this interaction"]})
            
            print("relationship found")



            print(f"relationship.agents: {relationship.agents}")
            robo_caller_agent = [agent for agent in relationship.agents if agent.name == "robo_caller_agent"][0]
            call_script = call_thread.conversation[-1].get('content')

            print(f"robo_caller_agent: {robo_caller_agent}")

            sender = call_thread.sender

            #call the make_robo_call task
            make_robo_call_task.delay(call_script, call_thread.select_phone_number(), call_thread.voter_id, call_thread.sender_id, call_thread.id)            

            return response, 200
        else:
            return response, 400

    except Exception as e:
        print(f"Exception: {e}")
        # add the error to the response
        return jsonify({'status': 'error', 'last_action': 'make_robo_call', 'errors': [str(e)]})
    


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
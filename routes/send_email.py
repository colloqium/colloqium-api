from flask import Blueprint, request, Response
# import Flask and other libraries
from flask import jsonify
from models.interaction import Interaction, InteractionStatus, SenderVoterRelationship
from context.database import db
from twilio.twiml.messaging_response import MessagingResponse
from tools.ai_functions.send_email import SendEmail
import json
import re

send_email_bp = Blueprint('send_email', __name__)

"""Route to send emails. Requires a json body with the following fields:
interaction_status: InteractionStatus.HUMAN_CONFIRMED
interaction_id: the id of the interaction to send a email for

The email needs to have been generated before this is called. This route will not generate a email.
TODO: Check if the email has been generated before sending it

Keyword arguments:
argument -- description
Return: return_description
"""

@send_email_bp.route("/send_email", methods=['POST', 'OPTIONS'])
def send_email():
    print("send_email route called")

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
        email_thread = db.session.query(Interaction).get(interaction_id)
        
        #set the interaction_status to InteractionStatus.HUMAN_CONFIRMED
        email_thread.interaction_status = InteractionStatus.HUMAN_CONFIRMED

        if email_thread:

            print("email_thread found")
            # get the planner for this email
            # tell the planner that the email has been human confirmed and is ready to be sent

            relationship = SenderVoterRelationship.query.filter_by(voter_id=email_thread.voter_id, sender_id=email_thread.sender_id).first()
            # filter the relationship.agents for an agent with the name planning_agent

            #if no relationship, return an error
            if not relationship:
                print("No relationship found for this interaction")
                return jsonify({'status': 'error', 'last_action': 'send_email', 'errors': ["No relationship found for this interaction"]})
            
            print("relationship found")

            body = ""

            while len(body) == 0 or body[0] != "{":
                print(f"relationship.agents: {relationship.agents}")
                email_agent = [agent for agent in relationship.agents if agent.name == "email_agent"][0]
                body = email_thread.conversation[-1].get('content')

                '''
                Check if the body of the response is a json object in the form

                {
                    "email_subject": "subject",
                    "email_body": "body"
                }

                if so, extract the email_subject and email_body from the json object
                '''

                if body[0] != "{":
                    email_agent.send_prompt("Please respond with a json object in the form: {\"email_subject\": \"subject\", \"email_body\": \"body\"} to send an email to the voter.")

            print("body is a json object")
            print(f"body: {body}")

            # Replace actual newline characters with escaped version, excluding those inside double quotes
            body = re.sub(r'(?<!")\n(?!")', '', body)

            # Replace the newlines inside double quotes with an aditional escape character
            body = re.sub(r'(?<=")\n(?=")', '\\\\n', body)


            print(f"body after replacing newlines and quotes: {body}")

            body = json.loads(body)
            print(f"body after json.loads: {body}")
            email_subject = body.get("subject")
            print(f"email_subject: {email_subject}")
            email_body = body.get("body")
            print(f"email_body: {email_body}")
            
            
            send_email = SendEmail()

            args = {
                "campaign_id": email_thread.campaign_id,
                "voter_id": email_thread.voter_id,
                "email_subject": email_subject,
                "email_body": email_body
            }

            send_email.call(**args)

            return response, 200
        else:
            return response, 400

    except Exception as e:
        print(f"Exception: {e}")
        # add the error to the response
        return jsonify({'status': 'error', 'last_action': 'send_email', 'errors': [str(e)]})
    


#Returns none or returns an array of error emails
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
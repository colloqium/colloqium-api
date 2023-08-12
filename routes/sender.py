'''
This file contains the routes for the sender. It can take a post request that will create a new sender and a get request that will return a list of all senders.

They should also be able to modify the sender with the post request if they have an existing sender id.
'''

from flask import Blueprint, json, request
# import Flask and other libraries
from flask import jsonify
from models.sender import Sender, PhoneNumber
from models.model_utility import get_phone_number_from_db
from tools.utility import format_phone_number
from context.database import db
# Import the functions from the other files


sender_bp = Blueprint('sender', __name__)


'''
API endroute for Sender

This API endpoint can be used to create, update and get senders.

The following parameters are required for each request type:
Create: A POST request that includes in the body: sender_name, sender_information, phone_numbers Where phone_numbers is an array of phone numbers from twilio
Returns a json object with the full sender object and a success code if successful:
{
    "sender": {
        "id": 1,
        "sender_name": "GOTV for All",
        "sender_information": "GOTV for all is a non partisan organization that is dedicated to getting out the vote for all people.",
        "phone_numbers": [+17706924459, +17706924458]
        //the rest of the sender fields
    },
    "status_code": 201
}

An example json object for a create request is:
{
    "sender_name": "GOTV for All",
    "sender_information": "GOTV for all is a non partisan organization that is dedicated to getting out the vote for all people.",
    "phone_numbers": ["+17706924459"]
}

Update: A PUT request that must include a  sender_id. If included sender_name, sender_information, phone_numbers will be updated if provided. Phone numbers will be added if provided. Other variables will be replaced if provided.
Returns a json object with the sender id and a success code if successful:
{
    "sender": {
        "id": 1
    },
    "status_code": 200
}

An example json object for an update request is:
{
    "sender_id": 1,
    "sender_name": "Edited GOTV for All",
    "sender_information": "Edited information",
    "phone_numbers": ["+17706924459", "+17706924458"]
}

Get: A GET request with the parameters passed in the query string. The following parameters are supported:
sender_id: The id of the sender to get
sender_name: The name of the sender to get
Returns a json object with the sender information and a success code if successful:
{
    "sender": {
        "id": 1,
    }
    "status_code": 200
}

An example query string for a get request is:
/sender?sender_id=1
/sender?sender_name=GOTV for All

'''
@sender_bp.route('/sender', methods=['GET', 'POST', 'PUT'])
def sender():

    # check if the content type of the request is json
    if request.method != 'GET' and not request.is_json:
        return jsonify({'error': 'Request body must be JSON', 'status_code': 400}), 400

    # check the type of request
    if request.method == 'POST':
        data = request.json
        return create_sender(data)
    elif request.method == 'PUT':
        data = request.json
        return update_sender(data)
    elif request.method == 'GET':
        data = request.args
        return get_sender(data)


def create_sender(data):

    sender_name = data['sender_name']
    sender_information = data['sender_information']
    #phone numbers is expected to be an array of phone numbers
    phone_numbers = data['phone_numbers']
    
    # check if sender already exists with the same name
    sender = Sender.query.filter_by(sender_name=sender_name).first()
    
    if sender:
        # return an http error code since the sender already exists
        return jsonify({'error': 'Sender already exists', 'status_code': 409}), 409
    
    #create PhoneNumber objects from the list of numbers shared
    processed_phone_numbers = [PhoneNumber(format_phone_number(phone_number)) for phone_number in phone_numbers]
    
    
    # create the sender
    sender = Sender(sender_name=sender_name,sender_information=sender_information)

    # add the sender to the database
    db.session.add(sender)
    db.session.commit()

    #retrieve the instantiated sender from the database
    sender = Sender.query.filter_by(sender_name=sender_name).first()

    #add the sender id to the phone numbers as a reference
    for phone_number in processed_phone_numbers:
        phone_number.sender_id = sender.id
        db.session.add(phone_number)
        db.session.commit()

    # return a success code and the created sender id
    return jsonify({'sender':{'id': sender.id}, 'status_code': 201}), 201



def update_sender(data):
    
    sender_id = data['sender_id']

    if not sender_id:
        return jsonify({'error': 'Sender id is required', 'status_code': 400}), 400
    
    sender = Sender.query.filter_by(id=sender_id).first()

    if not sender:
        return jsonify({'error': 'Sender does not exist', 'status_code': 404}), 404
    

    #update the sender name if it is provided
    if 'sender_name' in data.keys():
        #check if the sender name is already taken
        sender_name = data['sender_name']
        existing_sender = Sender.query.filter_by(sender_name=sender_name).first()
        if existing_sender:
            return jsonify({'error': 'Sender name already exists', 'status_code': 409}), 409
        sender.sender_name = sender_name

    #update the sender information if it is provided
    if 'sender_information' in data.keys():
        sender.sender_information = data['sender_information']
    
    #add any new phone numbers if they are provided
    if 'phone_numbers' in data.keys():
        phone_numbers = data['phone_numbers']
        processed_phone_numbers = [PhoneNumber(format_phone_number(phone_number)) for phone_number in phone_numbers]
        
        for phone_number in processed_phone_numbers:
            #make sure the phone number is not already in the database
            existing_phone_number = get_phone_number_from_db(phone_number.get_full_phone_number())

            if existing_phone_number:
                # include the taken phone number in the error message
                return jsonify({'error': 'Phone number already exists', 'status_code': 409, 'phone_number': existing_phone_number.get_full_phone_number()}), 409
            
            phone_number.sender_id = sender.id
            db.session.add(phone_number)
    
    db.session.add(sender)
    db.session.commit()

    # return success is true, the sender id and a success code
    return jsonify({'status': 'success',
    'sender': sender.to_dict(),
    'status_code': 200}), 200

def get_sender(data):
    
    # try to get the sender by the sender_name
    if 'sender_name' in data.keys():
        sender_name = data['sender_name']
        sender = Sender.query.filter_by(sender_name=sender_name).first()
        if not sender:
            return jsonify({'error': 'Sender with this name does not exist', 'status_code': 404}), 404
        return jsonify({'sender': sender.to_dict(), 'status_code': 200}), 200
    
    
    # try to get the sender by the sender_id
    if 'sender_id' in data.keys():
        # get the sender
        sender = Sender.query.filter_by(id=data['sender_id']).first()

        # check if the sender exists
        if not sender:
            return jsonify({'error': 'Sender with this ID does not exist', 'status_code': 404}), 404
        
        # return the sender information as a json object
        return jsonify({'sender': sender.to_dict(), 'status_code': 200}), 200
    
    # if no sender name or id is provided, return a list of all senders.
    senders = Sender.query.all()
    senders = [sender.to_dict() for sender in senders]
    return jsonify({'senders': senders, 'status_code': 200}), 200
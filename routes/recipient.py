# imports
from flask import Blueprint, jsonify, request, Response
from models.models import Recipient
from context.database import db
from tools.utility import format_phone_number
from context.analytics import analytics

# blueprint definition
recipient_bp = Blueprint('recipient', __name__)

@recipient_bp.route('/recipient', methods=['GET', 'POST', 'PUT', 'OPTIONS'])
def recipient():

    if request.method == 'OPTIONS':
        # Preflight request. Reply successfully:
        resp = Response(status=200)
        resp.headers['Access-Control-Allow-Origin'] = '*'
        resp.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, OPTIONS'
        resp.headers['Access-Control-Allow-Headers'] = 'content-type'
        return resp

    if request.method != 'GET' and not request.is_json:
        return jsonify({'error': 'Request body must be JSON', 'status_code': 400}), 400

    if request.method == 'GET':
        data = request.args
    else:
        data = request.json

    if request.method == 'POST':
        return create_recipient(data)
    elif request.method == 'PUT':
        return update_recipient(data)
    elif request.method == 'GET':
        return get_recipient(data)

def create_recipient(data):
    recipient_name = data['recipient_name']
    recipient_phone_number = data['recipient_phone_number']

    # Check if required fields are missing
    if not recipient_name or not recipient_phone_number:
        return jsonify({'error': 'Both recipient_name and recipient_phone_number are required', 'status_code': 400}), 400

    recipient = Recipient.query.filter_by(recipient_name=recipient_name).first()
    if recipient:
        return jsonify({'error': 'Recipient already exists', 'status_code': 409}), 409

    # Get optional attributes or set to None if they are not present
    recipient_information = data.get('recipient_information', None)
    recipient_profile = data.get('recipient_profile', None)
    recipient_engagement_history = data.get('recipient_engagement_history', None)

    recipient = Recipient(recipient_name=recipient_name, recipient_information=recipient_information, recipient_phone_number=format_phone_number(recipient_phone_number), recipient_profile=recipient_profile, recipient_engagement_history=recipient_engagement_history)

    db.session.add(recipient)
    db.session.commit()

    recipient = Recipient.query.filter_by(recipient_name=recipient_name).first()

    analytics.identify(recipient.id, {
        'name': recipient.recipient_name,
        'phone': recipient.recipient_phone_number
    })

    return jsonify({'recipient_id': recipient.id, 'status_code': 201}), 201


def update_recipient(data):

    recipient_id = data['recipient_id']
    if not recipient_id:
        return jsonify({'error': 'Recipient id is required', 'status_code': 400}), 400

    recipient = Recipient.query.filter_by(id=recipient_id).first()

    if not recipient:
        return jsonify({'error': 'Recipient does not exist', 'status_code': 404}), 404

    if 'recipient_phone_number' in data.keys():
        recipient_phone_number = data['recipient_phone_number']
        existing_recipient = Recipient.query.filter_by(recipient_phone_number=recipient_phone_number).first()
        if existing_recipient and existing_recipient.id != recipient_id:
            return jsonify({'error': 'Recipient with this phone number already exists', 'status_code': 409}), 409
        recipient.recipient_phone_number = recipient_phone_number

    if 'recipient_information' in data.keys():
        recipient.recipient_information = data['recipient_information']

    if 'recipient_name' in data.keys():
        recipient.recipient_name = data['recipient_name']

    if 'recipient_profile' in data.keys():
        recipient.recipient_profile = data['recipient_profile']

    if 'recipient_engagement_history' in data.keys():
        recipient.recipient_engagement_history = data['recipient_engagement_history']

    db.session.add(recipient)
    db.session.commit()

    return jsonify({'status': 'success', 'recipient_id': recipient.id, 'status_code': 200}), 200

def get_recipient(data):
    # Attempt to look up by recipient id
    if 'recipient_id' in data.keys():
        recipient_id = data['recipient_id']
        recipient = Recipient.query.filter_by(id=recipient_id).first()
        if not recipient:
            return jsonify({'error': 'Recipient does not exist', 'status_code': 404}), 404
        return jsonify({'recipient': recipient.to_dict(), 'status_code': 200}), 200
    
    # Attempt to look up by recipient phone number
    if 'recipient_phone_number' in data.keys():
        recipient_phone_number = format_phone_number(data['recipient_phone_number'])
        recipient = Recipient.query.filter_by(recipient_phone_number=recipient_phone_number).first()
        if not recipient:
            return jsonify({'error': 'Recipient with this phone number does not exist', 'status_code': 404}), 404
        return jsonify({'recipient': recipient.to_dict(), 'status_code': 200}), 200

    return jsonify({'error': 'No valid parameter provided', 'status_code': 400}), 400

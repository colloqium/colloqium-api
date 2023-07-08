# Route that handles audience related requests. Can create a new audience, add a recipient to an audience, or get all audiences assiciated with a sener

from flask import Blueprint, jsonify, request, Response
from models.models import Audience, Recipient
from context.database import db

# Create a new blueprint
audience_bp = Blueprint('audience', __name__)

@audience_bp.route('/audience', methods=['GET', 'POST', 'PUT', 'OPTIONS'])
def audience():
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
        return create_audience(data)
    elif request.method == 'PUT':
        return update_audience(data)
    elif request.method == 'GET':
        return get_audience(data)

def create_audience(data):
    audience_name = data.get('audience_name')
    sender_id = data.get('sender_id')

    # Check if required fields are missing
    if not all([audience_name, sender_id]):
        return jsonify({'error': 'Both audience_name and sender_id are required', 'status_code': 400}), 400

    audience = Audience.query.filter_by(audience_name=audience_name, sender_id=sender_id).first()
    if audience:
        return jsonify({'error': 'Audience already exists', 'status_code': 409}), 409

    audience = Audience(audience_name=audience_name, sender_id=sender_id)
    db.session.add(audience)
    db.session.commit()
    return jsonify({'status': 'success', 'audience':{ 'id': audience.id}, 'status_code': 201}), 201

def update_audience(data):
    audience_id = data.get('audience_id')

    # Check if audience_id is missing
    if not audience_id:
        return jsonify({'error': 'audience_id is required', 'status_code': 400}), 400

    audience = Audience.query.get(audience_id)
    if not audience:
        return jsonify({'error': 'Audience does not exist', 'status_code': 404}), 404

    # Check and update audience_name
    audience_name = data.get('audience_name')
    if audience_name:
        audience.audience_name = audience_name

    # Check and update audience_information
    audience_information = data.get('audience_information')
    if audience_information:
        audience.audience_information = audience_information

    # Check and update recipients
    recipient_ids = data.get('recipients')
    if recipient_ids:
        new_recipients = Recipient.query.filter(Recipient.id.in_(recipient_ids)).all()
        if new_recipients:
            # Create a new list merging the existing recipients and the new ones
            audience.recipients = list(set(audience.recipients + new_recipients))

    db.session.commit()

    return jsonify({'status': 'success', 'audience': {'id': audience.id}, 'status_code': 200}), 200


def get_audience(data):
    if 'sender_id' in data.keys():
        sender_id = data['sender_id']
        audiences = Audience.query.filter_by(sender_id=sender_id).all()
        return jsonify({'audiences': [audience.to_dict() for audience in audiences], 'status_code': 200}), 200
    elif 'recipient_id' in data.keys():
        recipient_id = data['recipient_id']
        recipient = Recipient.query.get(recipient_id)
        if not recipient:
            return jsonify({'error': 'Recipient does not exist', 'status_code': 404}), 404
        audiences = recipient.audiences
        return jsonify({'audiences': [audience.to_dict() for audience in audiences], 'status_code': 200}), 200
    elif 'audience_id' in data.keys():
        audience_id = data['audience_id']
        audience = Audience.query.get(audience_id)
        if not audience:
            return jsonify({'error': 'Audience does not exist', 'status_code': 404}), 404
        return jsonify({'audience': audience.to_dict(), 'status_code': 200}), 200

    return jsonify({'error': 'No valid parameter provided', 'status_code': 400}), 400

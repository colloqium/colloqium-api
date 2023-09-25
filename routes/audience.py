# Route that handles audience related requests. Can create a new audience, add a voter to an audience, or get all audiences assiciated with a sener

from flask import Blueprint, jsonify, request, Response
from models.sender import Audience, Campaign
from models.voter import Voter
from context.database import db

# Create a new blueprint
audience_bp = Blueprint('audience', __name__)

@audience_bp.route('/audience', methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
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
    elif request.method == 'DELETE':
        return delete_audience(data)

def create_audience(data):
    audience_name = data.get('audience_name')
    sender_id = data.get('sender_id')

    # Check if required fields are missing
    if not all([audience_name, sender_id]):
        return jsonify({'error': 'Both audience_name and sender_id are required', 'status_code': 400}), 400

    audience = Audience.query.filter_by(audience_name=audience_name, sender_id=sender_id).first()
    if audience:
        return jsonify({'error': 'Audience already exists', 'status_code': 409}), 409
    
    voters = []
    if 'voters' in data.keys():
        voter_ids = data['voters']
        print(voter_ids)
        voters = Voter.query.filter(Voter.id.in_(voter_ids)).all()


    campaigns = []
    if 'campaigns' in data.keys():
        campaign_ids = data['campaigns']
        campaigns = Campaign.query.filter(Campaign.id.in_(campaign_ids)).all()

    
    audience_information = None
    if 'audience_information' in data.keys():
        audience_information = data['audience_information']

    audience = Audience(audience_name=audience_name, audience_information=audience_information, sender_id=sender_id, voters=voters, campaigns=campaigns)
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
        existing_audience = Audience.query.filter_by(audience_name=audience_name, sender_id=audience.sender_id).first()
        if existing_audience and existing_audience.id != audience_id:
            return jsonify({'error': 'Audience name already exists for this sender', 'status_code': 409}), 409
        audience.audience_name = audience_name

    # Check and update audience_information
    audience_information = data.get('audience_information')
    if audience_information:
        audience.audience_information = audience_information

    # Check and update voters
    voter_ids = data.get('voters')
    if voter_ids:
        new_voters = Voter.query.filter(Voter.id.in_(voter_ids)).all()
        if new_voters:
            # Create a new list merging the existing voter and the new ones
            audience.voters = list(set(audience.voters + new_voters))

    campaign_ids = data.get('campaigns')
    if campaign_ids:
        new_campaigns = Campaign.query.filter(Campaign.id.in_(campaign_ids)).all()
        # make sure campaigns belong to the same sender
        for campaign in new_campaigns:
            if campaign.sender_id != audience.sender_id:
                return jsonify({'error': 'Campaign does not belong to this sender', 'status_code': 409}), 409
        if new_campaigns:
            # Create a new list merging the existing campaigns and the new ones
            audience.campaigns = list(set(audience.campaigns + new_campaigns))

    db.session.commit()

    return jsonify({'status': 'success', 'audience': audience.to_dict(), 'status_code': 200}), 200


def get_audience(data):
    if 'sender_id' in data.keys():
        sender_id = data['sender_id']
        audiences = Audience.query.filter_by(sender_id=sender_id).all()
        return jsonify({'audiences': [audience.to_dict() for audience in audiences], 'status_code': 200}), 200
    elif 'voter_id' in data.keys():
        voter_id = data['voter_id']
        voter = Voter.query.get(voter_id)
        if not voter:
            return jsonify({'error': 'voter does not exist', 'status_code': 404}), 404
        audiences = voter.audiences
        return jsonify({'audiences': [audience.to_dict() for audience in audiences], 'status_code': 200}), 200
    elif 'audience_id' in data.keys():
        audience_id = data['audience_id']
        audience = Audience.query.get(audience_id)
        if not audience:
            return jsonify({'error': 'Audience does not exist', 'status_code': 404}), 404
        return jsonify({'audience': audience.to_dict(), 'status_code': 200}), 200

    return jsonify({'error': 'No valid parameter provided', 'status_code': 400}), 400

def delete_audience(data):
    audience_id = data.get('audience_id')

    # Check if audience_id is missing
    if not audience_id:
        return jsonify({'error': 'audience_id is required', 'status_code': 400}), 400

    audience = Audience.query.get(audience_id)
    if not audience:
        return jsonify({'error': 'Audience does not exist', 'status_code': 404}), 404

    db.session.delete(audience)
    db.session.commit()

    return jsonify({'status': 'success', 'status_code': 200}), 200

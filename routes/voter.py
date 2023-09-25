# imports
from flask import Blueprint, jsonify, request, Response
from models.voter import Voter, VoterProfile
from context.database import db
from tools.utility import format_phone_number
from context.analytics import analytics

# blueprint definition
voter_bp = Blueprint('voter', __name__)

@voter_bp.route('/voter', methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
def voter():

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
        return create_voter(data)
    elif request.method == 'PUT':
        return update_voter(data)
    elif request.method == 'GET':
        return get_voter(data)
    elif request.method == 'DELETE':
        return delete_voter(data)

def create_voter(data):
    voter_name = data['voter_name']
    voter_phone_number = data['voter_phone_number']

    # Check if required fields are missing
    if not voter_name or not voter_phone_number:
        return jsonify({'error': 'Both voter_name and voter_phone_number are required', 'status_code': 400}), 400

    cleaned_phone_number = format_phone_number(voter_phone_number)

    voter = Voter.query.filter_by(voter_name=voter_name, voter_phone_number=cleaned_phone_number).first()
    if voter:
        return jsonify({'error': 'voter already exists', 'status_code': 409}), 409

    voter = Voter(voter_name=voter_name, voter_phone_number=cleaned_phone_number)

    db.session.add(voter)
    db.session.commit()

    voter = Voter.query.filter_by(voter_name=voter_name).first()

    if not voter:
        return jsonify({'error': 'voter could not be created', 'status_code': 500}), 500

    voter_profile = data['voter_profile']
    

    profile_object = VoterProfile(voter_id=voter.id)
    
    # Request may contain voter profile which will be a json object that contains at least one of interests, policy preferences, or preferred contact method
    if voter_profile:
        profile_object.interests = voter_profile['interests'] if 'interests' in voter_profile.keys() else None
        profile_object.policy_preferences = voter_profile['policy_preferences'] if 'policy_preferences' in voter_profile.keys() else None
        profile_object.preferred_contact_method = voter_profile['preferred_contact_method'] if 'preferred_contact_method' in voter_profile.keys() else None

    db.session.add(profile_object)
    db.session.commit()

    analytics.identify(voter.id, {
        'name': voter.voter_name,
        'phone': voter.voter_phone_number
    })

    return jsonify({ 
        'voter': {
            'id': voter.id,
        }, 'status_code': 201}), 201


def update_voter(data):

    voter_id = data['voter_id']
    if not voter_id:
        return jsonify({'error': 'voter id is required', 'status_code': 400}), 400

    voter = Voter.query.filter_by(id=voter_id).first()

    if not voter:
        return jsonify({'error': 'voter does not exist', 'status_code': 404}), 404

    if 'voter_phone_number' in data.keys():
        voter_phone_number = data['voter_phone_number']
        existing_voter = Voter.query.filter_by(voter_phone_number=voter_phone_number).first()
        if existing_voter and existing_voter.id != voter_id:
            return jsonify({'error': 'voter with this phone number already exists', 'status_code': 409}), 409
        voter.voter_phone_number = voter_phone_number

    if 'voter_name' in data.keys():
        voter.voter_name = data['voter_name']

    if 'voter_profile' in data.keys():
        voter_profile = VoterProfile.query.filter_by(voter_id=voter_id).first()

        if not voter_profile:
            # create a voter profile and attach it to the voter
            voter_profile = VoterProfile(voter_id=voter_id)
            db.session.add(voter_profile)
            db.session.commit()

            #check if voter profile was created
            voter_profile = VoterProfile.query.filter_by(voter_id=voter_id).first()
            if not voter_profile:
                return jsonify({'error': 'voter profile could not be created', 'status_code': 500}), 500
        
        if 'interests' in data['voter_profile'].keys():
            voter_profile.interests = data['voter_profile']['interests']
        
        if 'policy_preferences' in data['voter_profile'].keys():
            voter_profile.policy_preferences = data['voter_profile']['policy_preferences']

        if 'preferred_contact_method' in data['voter_profile'].keys():
            voter_profile.preferred_contact_method = data['voter_profile']['preferred_contact_method']

    db.session.add(voter)
    db.session.commit()

    return jsonify({'status': 'success', 'voter': voter.to_dict(), 'status_code': 200}), 200

def get_voter(data):
    # Attempt to look up by voter id
    if 'voter_id' in data.keys():
        voter_id = data['voter_id']
        voter = Voter.query.filter_by(id=voter_id).first()
        if not voter:
            return jsonify({'error': 'voter does not exist', 'status_code': 404}), 404
        return jsonify({'voter': voter.to_dict(), 'status_code': 200}), 200
    
    # Attempt to look up by voter phone number
    if 'voter_phone_number' in data.keys():
        voter_phone_number = format_phone_number(data['voter_phone_number'])
        voter = Voter.query.filter_by(voter_phone_number=voter_phone_number).first()
        if not voter:
            return jsonify({'error': 'voter with this phone number does not exist', 'status_code': 404}), 404
        return jsonify({'voter': voter.to_dict(), 'status_code': 200}), 200

    return jsonify({'error': 'No valid parameter provided', 'status_code': 400}), 400

def delete_voter(data):
    if 'voter_id' not in data.keys():
        return jsonify({'error': 'voter id is required', 'status_code': 400}), 400

    voter = Voter.query.filter_by(id=data['voter_id']).first()

    if not voter:
        return jsonify({'error': 'voter does not exist', 'status_code': 404}), 404

    db.session.delete(voter)
    db.session.commit()

    return jsonify({'status': 'success', 'status_code': 200}), 200

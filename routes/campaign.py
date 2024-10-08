from flask import Blueprint, jsonify, request
from models.sender import Campaign, Sender, Audience
from context.database import db
from datetime import datetime

# blueprint definition
campaign_bp = Blueprint('campaign', __name__)

@campaign_bp.route('/campaign', methods=['GET', 'POST', 'PUT', 'DELETE'])
def campaign():

    # check if the content type of the request is json
    if request.method != 'GET' and not request.is_json:
        return jsonify({'error': 'Request body must be JSON', 'status_code': 400}), 400

    if request.method == 'POST':
        data = request.json
        return create_campaign(data)
    elif request.method == 'PUT':
        data = request.json
        return update_campaign(data)
    elif request.method == 'GET':
        data = request.args
        return get_campaign(data)
    elif request.method == 'DELETE':
        data = request.json
        return delete_campaign(data)

def create_campaign(data):
    campaign_name = data['campaign_name']
    sender_id = data['sender_id']

    # Check if required fields are missing
    if not campaign_name or not sender_id:
        return jsonify({'error': 'Both campaign_name and sender_id are required', 'status_code': 400}), 400

    # Check if the sender exists
    sender = Sender.query.filter_by(id=sender_id).first()

    if not sender:
        return jsonify({'error': 'Sender does not exist', 'status_code': 404}), 404

    campaign = Campaign.query.filter_by(campaign_name=campaign_name, sender_id=sender.id).first()
    if campaign:
        return jsonify({'error': 'Campaign already exists for this sender', 'status_code': 409}), 409

    # Get optional attributes or set to None if they are not present
    campaign_prompt = data.get('campaign_prompt', None)
    campaign_goal = data.get('campaign_goal', None)
    campaign_end_date = data.get('campaign_end_date', None)
    audience_ids = data.get('audiences', None)
    campaign_type = data.get('campaign_type', None)

    # Parse campaign end date if provided
    if campaign_end_date:
        campaign_end_date = campaign_end_date.split('T')[0]
        campaign_end_date = datetime.strptime(campaign_end_date, '%Y-%m-%d').date()

    # Get Audience objects from provided IDs
    audiences = None
    if audience_ids:
        audiences = Audience.query.filter(Audience.id.in_(audience_ids)).all()

    campaign = Campaign(
        campaign_name=campaign_name, 
        campaign_prompt=campaign_prompt, 
        campaign_goal=campaign_goal, 
        sender_id=sender_id, 
        campaign_end_date=campaign_end_date,
        campaign_type=campaign_type
    )

    if audiences:
        campaign.audiences = audiences

    db.session.add(campaign)
    db.session.commit()

    campaign = Campaign.query.filter_by(campaign_name=campaign_name).first()

    return jsonify({'campaign': { 'id': campaign.id}, 'status_code': 201}), 201


def update_campaign(data):
    campaign_id = data['campaign_id']
    if not campaign_id:
        return jsonify({'error': 'Campaign id is required', 'status_code': 400}), 400

    campaign = Campaign.query.filter_by(id=campaign_id).first()

    if not campaign:
        return jsonify({'error': 'Campaign does not exist', 'status_code': 404}), 404

    if 'campaign_name' in data.keys():
        #check if the campaign name already exists for this sender
        campaign_name = data['campaign_name']
        sender_id = campaign.sender_id
        existing_campaign = Campaign.query.filter_by(campaign_name=campaign_name, sender_id=sender_id).first()
        if existing_campaign:
            if existing_campaign.id != campaign.id:
                return jsonify({'error': 'Campaign with this name already exists for this sender', 'status_code': 409}), 409

        campaign.campaign_name = data['campaign_name']

    if 'campaign_prompt' in data.keys():
        campaign.campaign_prompt = data['campaign_prompt']

    if 'sender_id' in data.keys():
        # sender name should not be changed
        return jsonify({'error': 'Sender name cannot be changed', 'status_code': 400}), 400

    if 'campaign_end_date' in data.keys():
        campaign.campaign_end_date = datetime.strptime(data['campaign_end_date'], '%Y-%m-%d').date()

    if 'campaign_goal' in data.keys():
        campaign.campaign_goal = data['campaign_goal']

    if 'campaign_type' in data.keys():
        campaign.campaign_type = data['campaign_type']

    if 'audiences' in data.keys():
        #get audiences from the ids in the array
        audiences = Audience.query.filter(Audience.id.in_(data['audiences'])).all()

        # add audiences to the campaign
        for audience in audiences:
            # check if the audience is owned by the same sender
            if audience.sender_id != campaign.sender_id:
                return jsonify({'error': 'Audience does not belong to this sender', 'status_code': 409}), 409
            if audience not in campaign.audiences:
                campaign.audiences.append(audience)
        print(campaign.audiences)

    if 'campaign_manager_summary' in data.keys():
        campaign.campaign_manager_summary = data['campaign_manager_summary']

    if 'communications_director_summary' in data.keys():
        campaign.communications_director_summary = data['communications_director_summary']

    if 'field_director_summary' in data.keys():
        campaign.field_director_summary = data['field_director_summary']

    if 'interactions_sent' in data.keys():
        campaign.interactions_sent = data['interactions_sent']

    if 'interactions_delivered' in data.keys():
        campaign.interactions_delivered = data['interactions_delivered']

    if 'interactions_responded' in data.keys():
        campaign.interactions_responded = data['interactions_responded']

    if 'interactions_converted' in data.keys():
        campaign.interactions_converted = data['interactions_converted']

    db.session.add(campaign)
    db.session.commit()

    return jsonify({'status': 'success', 'campaign': {'id': campaign.id}, 'status_code': 200}), 200

def get_campaign(data):
    # Look for a sender id. If there is one, get all campaign IDs for that sender
    if 'sender_id' in data.keys():
        sender = Sender.query.filter_by(id=data['sender_id']).first()

        if not sender:
            return jsonify({'error': 'Sender does not exist', 'status_code': 404}), 404

        campaign_ids = db.session.query(Campaign.id).filter_by(sender_id=sender.id).all()
        campaign_ids = [id[0] for id in campaign_ids]  # Flatten the list of tuples

        return jsonify({'campaign_ids': campaign_ids, 'status_code': 200}), 200
    
    # look for a campaign based on the campaign id
    if 'campaign_id' in data.keys():
        try:
            campaign_id = int(data['campaign_id'])
            campaign = Campaign.query.filter_by(id=campaign_id).first()
        except (ValueError, KeyError):
            return jsonify({'error': 'Invalid campaign_id', 'status_code': 400}), 400

        if not campaign:
            return jsonify({'error': 'Campaign does not exist', 'status_code': 404}), 404

        return jsonify({'campaign': campaign.to_dict(), 'status_code': 200}), 200
    
    # return a list of all campaign IDs
    campaign_ids = db.session.query(Campaign.id).all()
    campaign_ids = [id[0] for id in campaign_ids]  # Flatten the list of tuples
    return jsonify({'campaign_ids': campaign_ids, 'status_code': 200}), 200

def delete_campaign(data):
    print(f"Calling delete campaign at {datetime.now()} with data: {data}")
    if 'campaign_id' not in data.keys():
        return jsonify({'error': 'Campaign id is required', 'status_code': 400}), 400

    campaign = Campaign.query.filter_by(id=data['campaign_id']).first()

    if not campaign:
        return jsonify({'error': 'Campaign does not exist', 'status_code': 404}), 404

    db.session.delete(campaign)
    db.session.commit()

    print(f"Deleted campaign at {datetime.now()}")

    return jsonify({'status': 'success', 'status_code': 200}), 200
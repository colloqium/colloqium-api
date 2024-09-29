from flask import Blueprint, request, jsonify
# import Flask and other libraries
from models.interaction import Interaction, InteractionStatus
from context.database import db
from sqlalchemy.orm import load_only
from sqlalchemy import update
from tasks.create_interactions_from_campaign import create_interactions_from_campaign


interaction_bp = Blueprint('interaction', __name__)

@interaction_bp.route('/interaction', methods=['POST', 'PUT', 'GET'])
def interaction():
    
    data = None
    if request.method != 'GET':
        if not request.is_json:
            return jsonify({'error': 'Request body must be JSON', 'status_code': 400}), 400
        data = request.json
    else:
        data = request.args

    if request.method == 'GET':
        return get_interaction(data)
    elif request.method == 'POST':
        print(data)
        return create_interaction(data)
    elif request.method == 'PUT':
        return update_interaction(data)

def create_interaction(data):

    print("Creating interaction")

    campaign_id = None

    if 'campaign_id' in data.keys():
        campaign_id = data['campaign_id']
    

    if 'interaction_type' not in data.keys():
        return jsonify({'error': 'interaction_type is required', 'status_code': 400}), 400

    interaction_type = data['interaction_type']

    # Check if required fields are missing
    if not interaction_type:
        return jsonify({'error': 'interaction_type is required', 'status_code': 400}), 400
    
    if not campaign_id:
        return jsonify({'error': 'campaign_id is required', 'status_code': 400}), 400

    create_interactions_from_campaign.apply_async(args=[campaign_id, interaction_type])
    return jsonify({'message': 'Interactions created', 'status_code': 200}), 200

def get_interaction(data):
    #Check if there is a sender id. If there is return all interaction IDs for that sender
    if 'sender_id' in data.keys():
        sender_id = data['sender_id']

        interaction_ids = db.session.query(Interaction.id).filter_by(sender_id=sender_id).all()
        interaction_ids = [id[0] for id in interaction_ids]  # Flatten the list of tuples
        if not interaction_ids:
            return jsonify({'error': 'Sender does not have any interactions', 'status_code': 404}), 404
        return jsonify({'interaction_ids': interaction_ids, 'status_code': 200}), 200

    #Check if there is a voter id. If there is return all interaction IDs for that voter
    if 'voter_id' in data.keys():
        voter_id = data['voter_id']
        interaction_ids = db.session.query(Interaction.id).filter_by(voter_id=voter_id).all()
        interaction_ids = [id[0] for id in interaction_ids]  # Flatten the list of tuples
        if not interaction_ids:
            return jsonify({'error': 'Voter does not have any interactions', 'status_code': 404}), 404
        return jsonify({'interaction_ids': interaction_ids, 'status_code': 200}), 200
    
    #Check if there is a campaign id. If there is return all interaction IDs for that campaign
    if 'campaign_id' in data.keys():
        campaign_id = data['campaign_id']
        min_interaction_status = data.get('min_interaction_status', InteractionStatus.CREATED)
        max_interaction_status = data.get('max_interaction_status', InteractionStatus.CONVERTED)

        if int(min_interaction_status) < InteractionStatus.CREATED or int(max_interaction_status) > InteractionStatus.CONVERTED:
            return jsonify({'error': f'Your min interaction status is outside of the valid range from {InteractionStatus.CREATED} for created interactions to {InteractionStatus.CONVERTED} for converted interactions', 'status_code': 400}), 400

        # get the interactions with a status  greater than or equal to the interaction_status
        interaction_ids = db.session.query(Interaction.id).filter(Interaction.campaign_id==campaign_id, Interaction.interaction_status>=min_interaction_status, Interaction.interaction_status<=max_interaction_status).all()

        interaction_ids = [id[0] for id in interaction_ids]  # Flatten the list of tuples
        if not interaction_ids:
            return jsonify({'error': 'Campaign does not have any interactions', 'status_code': 404}), 404
        return jsonify({'interaction_ids': interaction_ids, 'status_code': 200}), 200
    
    #Check if there is an interaction id. If there is return that interaction
    if 'interaction_id' in data.keys():
        interaction_id = data['interaction_id']
        interaction = Interaction.query.get(interaction_id)
        if not interaction:
            return jsonify({'error': 'Interaction does not exist', 'status_code': 404}), 404
        return jsonify({'interaction': interaction.to_dict(), 'status_code': 200}), 200

    return jsonify({'error': 'No valid query parameters', 'status_code': 400}), 400

def update_interaction(data):
    print("Updating interaction")
    interaction_id = data['interaction_id']
    
    with db.session.no_autoflush:
        # Load only the necessary columns
        interaction = Interaction.query.options(load_only('id', 'conversation', 'interaction_status')).get(interaction_id)
        if not interaction:
            return jsonify({'error': 'Interaction does not exist', 'status_code': 404}), 404

        changes = {}

        if 'interaction_status' in data:
            interaction_status = data['interaction_status']
            if int(interaction_status) < InteractionStatus.CREATED or int(interaction_status) > InteractionStatus.CONVERTED:
                return jsonify({'error': f'Your interaction status is outside of the valid range from {InteractionStatus.CREATED} for created interactions to {InteractionStatus.CONVERTED} for converted interactions', 'status_code': 400}), 400
            changes['interaction_status'] = interaction_status

        if 'last_message' in data:
            conversation = interaction.conversation.copy() if interaction.conversation else []
            if conversation:
                conversation[-1]['content'] = data['last_message']
            else:
                conversation = [{'role': 'assistant', 'content': data['last_message']}]
            changes['conversation'] = conversation
            print(f"Updated conversation: {conversation}")

        if changes:
            # Use update() to directly update the database
            db.session.execute(
                update(Interaction).
                where(Interaction.id == interaction_id).
                values(**changes)
            )
            db.session.commit()

        # Refresh the interaction object to ensure we have the latest data
        db.session.refresh(interaction)

        print(f"Updated interaction: {interaction.to_dict()}")

    return jsonify({'interaction': interaction.to_dict(), 'status_code': 200}), 200
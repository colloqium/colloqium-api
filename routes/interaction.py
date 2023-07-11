from flask import Blueprint, request, jsonify, current_app
# import Flask and other libraries
from models.models import Recipient, Campaign, Interaction, InteractionStatus
from context.constants import INTERACTION_TYPES
from tools.utility import add_llm_response_to_conversation, initialize_conversation
from context.database import db
# Import the functions from the other files
from context.analytics import analytics, EVENT_OPTIONS
from tools.scheduler import scheduler
from datetime import datetime, timedelta


interaction_bp = Blueprint('interaction', __name__)

@interaction_bp.route('/interaction', methods=['POST', 'GET'])
def interaction():
    
    if request.method != 'GET' and not request.is_json:
        return jsonify({'error': 'Request body must be JSON', 'status_code': 400}), 400

    if request.method == 'GET':
        data = request.args
        return get_interaction(data)
    else:
        data = request.json
        print(data)
        return create_interaction(data)



def create_interaction(data):
    campaign_id = data['campaign_id']
    interaction_type = data['interaction_type']

    # Check if required fields are missing
    if not campaign_id or not interaction_type:
        return jsonify({'error': 'campaign_id, and interaction_type are all required', 'status_code': 400}), 400
    
    #check if an audience is provided, if so, create an interaction for each recipient in the audience

    campaign = Campaign.query.get(campaign_id)
    audiences = campaign.audiences
    if audiences:
        with current_app.app_context():
            scheduler.start()
        interactions = []
        for audience in audiences:
            recipients = audience.recipients
            for recipient in recipients:
                interaction = build_interaction(recipient, campaign, interaction_type)

                #check if an interaction already exists for this recipient and campaign
                #if so, do not create a new interaction
                existing_interaction = Interaction.query.filter_by(recipient_id=recipient.id, campaign_id=campaign.id).first()
                if existing_interaction:
                    print("Interaction already exists for this recipient and campaign")
                    continue 

                db.session.add(interaction)
                db.session.commit()


                # Schedule the interaction initialization for .1 seconds from now
                scheduler.add_job(
                    func=initialize_interaction,
                    args=[interaction.id, current_app._get_current_object()],
                    id=f'initialize-interaction-{interaction.id}'
                )
                # Initialize interaction
                interactions.append(interaction)

        return jsonify({
            "status_code": 201,
            "interactions": {'interaction': {'id': interaction.id} for interaction in interactions}
            }), 201

    return jsonify({'error': 'Campaign does not have an audience', 'status_code': 404}), 404

# Creates a new interaction with a recipient and the first system message in the conversation. Does not send the message.
def initialize_interaction(interaction_id, app):
    
    with app.app_context():
        interaction = Interaction.query.get(interaction_id)

        if not interaction:
            print("Interaction does not exist")
            return
        
        print("Initializing interaction from scheduler")
        interaction_type = interaction.interaction_type

        system_prompt = INTERACTION_TYPES[interaction_type].system_initialization_method(interaction)

        user_number = interaction.recipient.recipient_phone_number
        sender_number = interaction.sender.select_phone_number_for_interaction(interaction)

        # Pre-create the first response
        conversation = initialize_conversation(system_prompt)
        interaction.conversation = conversation
        initial_statement = add_llm_response_to_conversation(interaction)
        print("Interaction created successfully")
        interaction.interaction_status = InteractionStatus.INITIALIZED


        db.session.add(interaction)
        db.session.commit()

        analytics.track(interaction.recipient.id, EVENT_OPTIONS.initialized, {
            'sender_id': interaction.sender.id,
            'sender_phone_number': sender_number,
            'interaction_type': interaction.interaction_type,
            'interaction_id': interaction.id
        })

        # Log the system prompt and user number
        print("Interaction Type: %s", interaction_type)
        print(f"System prompt: {system_prompt}")
        print(f"User number: {user_number}")
        print(f"Sender number: {sender_number}")
        print(f"Initial Statement: {initial_statement}")
        print(f"Conversation: {conversation}")

def get_interaction(data):
    #Check if there is a sender id. If there is return all interactions for that sender
    if 'sender_id' in data.keys():
        sender_id = data['sender_id']

        interactions = Interaction.query.filter_by(sender_id=sender_id).all()
        if not interactions:
            return jsonify({'error': 'Sender does not have any interactions', 'status_code': 404}), 404
        return jsonify([interaction.to_dict() for interaction in interactions]), 200

    #Check if there is a recipient id. If there is return all interactions for that recipient
    if 'recipient_id' in data.keys():
        recipient_id = data['recipient_id']
        interactions = Interaction.query.filter_by(recipient_id=recipient_id).all()
        if not interactions:
            return jsonify({'error': 'Recipient does not have any interactions', 'status_code': 404}), 404
        return jsonify([interaction.to_dict() for interaction in interactions]), 200
    
    #Check if there is a campaign id. If there is return all interactions for that campaign
    if 'campaign_id' in data.keys():
        campaign_id = data['campaign_id']
        interactions = Interaction.query.filter_by(campaign_id=campaign_id).all()
        if not interactions:
            return jsonify({'error': 'Campaign does not have any interactions', 'status_code': 404}), 404
        return jsonify([interaction.to_dict() for interaction in interactions]), 200
    
    #Check if there is an interaction id. If there is return that interaction
    if 'interaction_id' in data.keys():
        interaction_id = data['interaction_id']
        interaction = Interaction.query.get(interaction_id)
        if not interaction:
            return jsonify({'error': 'Interaction does not exist', 'status_code': 404}), 404
        return jsonify(interaction.to_dict()), 200

    return jsonify({'error': 'No valid query parameters', 'status_code': 400}), 400

def build_interaction(recipient: Recipient, campaign: Campaign, interaction_type: str) -> Interaction:
    if not recipient:
        return jsonify({'error': 'Recipient does not exist', 'status_code': 404}), 404

    if not campaign:
        return jsonify({'error': 'Campaign does not exist', 'status_code': 404}), 404
    
    # check if the interaction types is in the keys of INTERACTION_TYPES
    if interaction_type not in INTERACTION_TYPES.keys():
        return jsonify({'error': 'Invalid interaction type', 'status_code': 400}), 400

    # Create new interaction
    return Interaction(
        recipient_id=recipient.id,
        sender_id=campaign.sender_id,
        campaign_id=campaign.id,
        interaction_type=interaction_type,
        interaction_status=InteractionStatus.CREATED
    )
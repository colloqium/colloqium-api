from flask import Blueprint, request, jsonify, current_app
# import Flask and other libraries
from models.voter import Voter
from models.sender import Campaign
from models.interaction import Interaction, InteractionStatus
from models.interaction_types import INTERACTION_TYPES
from tools.utility import get_llm_response_to_conversation, initialize_conversation
from context.database import db
# Import the functions from the other files
from context.analytics import analytics, EVENT_OPTIONS
from context.sockets import socketio
import threading
import json


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

    print("Creating interaction")

    campaign_id = None
    voter_id = None

    if 'campaign_id' in data.keys():
        campaign_id = data['campaign_id']

    if 'voter_id' in data.keys():
        voter_id = data['voter_id']
    
    interaction_type = data['interaction_type']

    # Check if required fields are missing
    if not interaction_type:
        return jsonify({'error': 'interaction_type is required', 'status_code': 400}), 400
    
    #check if an audience is provided, if so, create an interaction for each voter in the audience

    if campaign_id:
        print("Creating interaction for campaign")
        campaign = Campaign.query.get(campaign_id)
        audiences = campaign.audiences
        if audiences:
            print("Campaign has an audience")
            interactions = []
            for audience in audiences:
                voters = audience.voters
                for voter in voters:
                    print(f"Creating interaction for voter {voter.id}")
                    #check if an interaction already exists for this voter and campaign
                    #if so, do not create a new interaction
                    existing_interaction = Interaction.query.filter_by(voter_id=voter.id, campaign_id=campaign.id).first()
                    if existing_interaction:
                        print("Interaction already exists for this voter and campaign")
                        continue 

                    interaction = build_interaction(voter=voter, interaction_type=interaction_type, campaign=campaign)

                    #check if interaction is an Interaction object, if not there was an error
                    if not isinstance(interaction, Interaction):
                        return interaction

                    db.session.add(interaction)
                    db.session.commit()

                    thread = threading.Thread(target=initialize_interaction, args=[interaction.id, current_app._get_current_object()])
                    thread.start()
                    print("Interaction created successfully and thread started")

                    # Initialize interaction
                    interactions.append(interaction)

            return jsonify({
                "status_code": 201,
                "interactions": {'interaction': {'id': interaction.id} for interaction in interactions}
                }), 201
        else:
            return jsonify({'error': 'Campaign does not have an audience', 'status_code': 404}), 404
    
    if voter_id:
        voter = Voter.query.get(voter_id)
        if not voter:
            return jsonify({'error': 'Voter does not exist', 'status_code': 404}), 404
        interaction = build_interaction(voter=voter, interaction_type=interaction_type)
        db.session.add(interaction)
        db.session.commit()

        thread = threading.Thread(target=initialize_interaction, args=[interaction.id, current_app._get_current_object()])
        thread.start()

        return jsonify({
            "status_code": 201,
            "interaction": {'id': interaction.id}
            }), 201

# Creates a new interaction with a voter and the first system message in the conversation. Does not send the message.
def initialize_interaction(interaction_id, app):
    
    with app.app_context():
        print(f"Initializing interaction {interaction_id}")
        interaction = Interaction.query.get(interaction_id)

        if not interaction:
            print("Interaction does not exist")
            return
        
        print("Initializing interaction from scheduler")
        interaction_type = interaction.interaction_type

        system_prompt = INTERACTION_TYPES[interaction_type].system_initialization_method(interaction)

        user_number = interaction.voter.voter_phone_number
        sender_number = interaction.select_phone_number_for_interaction()

        # Pre-create the first response
        conversation = initialize_conversation(system_prompt)
        interaction.conversation = conversation
        initial_statement = get_llm_response_to_conversation(conversation)
        interaction.conversation.append(initial_statement)
        print("Interaction created successfully")
        interaction.interaction_status = InteractionStatus.INITIALIZED


        db.session.add(interaction)
        db.session.commit()

        # Send a message to all open WebSocket connections with a matching campaign_id
        socketio.emit('interaction_initialized', {'interaction_id': interaction.id, 'campaign_id': interaction.campaign_id}, room=f'subscribe_campaign_initialization_{interaction.campaign_id}')
        socketio.emit('interaction_initialized', {'interaction_id': interaction.id, 'sender_id': interaction.sender_id}, room=f'subscribe_sender_confirmation_{interaction.sender_id}')


        analytics.track(interaction.voter.id, EVENT_OPTIONS.initialized, {
            'sender_id': interaction.sender.id,
            'sender_phone_number': sender_number,
            'interaction_type': interaction.interaction_type,
            'interaction_id': interaction.id
        })

        # Log the system prompt and user number
        print("Interaction Type: %s", interaction_type)
        print(f"User number: {user_number}")
        print(f"Sender number: {sender_number}")
        print(f"Initial Statement: {initial_statement}")

def get_interaction(data):
    #Check if there is a sender id. If there is return all interactions for that sender
    if 'sender_id' in data.keys():
        sender_id = data['sender_id']

        interactions = Interaction.query.filter_by(sender_id=sender_id).all()
        if not interactions:
            return jsonify({'error': 'Sender does not have any interactions', 'status_code': 404}), 404
        return jsonify({'interactions': [interaction.to_dict() for interaction in interactions], 'status_code': 200}), 200

    #Check if there is a voter id. If there is return all interactions for that voter
    if 'voter_id' in data.keys():
        voter_id = data['voter_id']
        interactions = Interaction.query.filter_by(voter_id=voter_id).all()
        if not interactions:
            return jsonify({'error': 'voter does not have any interactions', 'status_code': 404}), 404
        return jsonify({'interactions': [interaction.to_dict() for interaction in interactions], 'status_code': 200}), 200
    
    #Check if there is a campaign id. If there is return all interactions for that campaign
    if 'campaign_id' in data.keys():
        campaign_id = data['campaign_id']
        interactions = Interaction.query.filter_by(campaign_id=campaign_id).all()
        if not interactions:
            return jsonify({'error': 'Campaign does not have any interactions', 'status_code': 404}), 404
        return jsonify({'interactions': [interaction.to_dict() for interaction in interactions], 'status_code': 200}), 200
    
    #Check if there is an interaction id. If there is return that interaction
    if 'interaction_id' in data.keys():
        interaction_id = data['interaction_id']
        interaction = Interaction.query.get(interaction_id)
        if not interaction:
            return jsonify({'error': 'Interaction does not exist', 'status_code': 404}), 404
        return jsonify({'interaction': interaction.to_dict(), 'status_code': 200}), 200

    return jsonify({'error': 'No valid query parameters', 'status_code': 400}), 400

def build_interaction(voter: Voter, interaction_type: str, campaign: Campaign = None) -> Interaction:
    if not voter:
        print("Voter does not exist for interaction")
        return jsonify({'error': 'voter does not exist', 'status_code': 404}), 404
    
    # check if the interaction types is in the keys of INTERACTION_TYPES
    if interaction_type not in INTERACTION_TYPES.keys():
        print("Invalid interaction type")
        print(f"Interaction type keys: {INTERACTION_TYPES.keys()}")
        print(f"Interaction type: {interaction_type}")
        return jsonify({'error': 'Invalid interaction type', 'status_code': 400}), 400

    # Create new interaction
    interaction = Interaction(
        voter_id=voter.id,
        interaction_type=interaction_type,
        interaction_status=InteractionStatus.CREATED
    )

    # If a campaign is provided, add it to the interaction
    if campaign:
        interaction.campaign_id = campaign.id
        interaction.sender_id = campaign.sender_id

    return interaction
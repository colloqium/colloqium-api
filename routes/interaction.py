from flask import Blueprint, request, jsonify, current_app
# import Flask and other libraries
from models.voter import Voter
from models.sender import Campaign
from models.interaction import Interaction, InteractionStatus, SenderVoterRelationship
from models.interaction_types import INTERACTION_TYPES
from models.ai_agents.planner_agent import PlannerAgent
from models.ai_agents.agent import Agent
from tools.utility import get_llm_response_to_conversation, initialize_conversation
from context.database import db
# Import the functions from the other files
from context.analytics import analytics, EVENT_OPTIONS
from context.sockets import socketio
import threading
import json


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
    voter_id = None

    if 'campaign_id' in data.keys():
        campaign_id = data['campaign_id']
    
    interaction_type = data['interaction_type']

    # Check if required fields are missing
    if not interaction_type:
        return jsonify({'error': 'interaction_type is required', 'status_code': 400}), 400
    
    if not campaign_id:
        return jsonify({'error': 'campaign_id is required', 'status_code': 400}), 400

    print("Creating interaction for campaign")
    campaign = Campaign.query.get(campaign_id)
    audiences = campaign.audiences

    if not audiences:
        print("Campaign does not have an audience")
        return jsonify({'error': 'Campaign does not have an audience', 'status_code': 404}), 404


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

# Creates a new interaction with a voter and the first system message in the conversation. Does not send the message.
def initialize_interaction(interaction_id, app):
    
    with app.app_context():

        print(f"Initializing interaction {interaction_id}")
        interaction = Interaction.query.get(interaction_id)

        if not interaction:
            print("Interaction does not exist")
            return
        
        sender_voter_relationship = SenderVoterRelationship.query.filter_by(sender_id=interaction.sender_id, voter_id=interaction.voter_id).first()

        if not sender_voter_relationship:
            sender_voter_relationship = SenderVoterRelationship(sender_id=interaction.sender_id, voter_id=interaction.voter_id)
            db.session.add(sender_voter_relationship)
            db.session.commit()
            # get the hydrated sender_voter_relationship
            sender_voter_relationship = SenderVoterRelationship.query.filter_by(sender_id=interaction.sender_id, voter_id=interaction.voter_id).first()

        # look for an agent with the name Planner Agent in the sender_voter_relationship
        planner_agent = Agent.query.filter_by(sender_voter_relationship_id=sender_voter_relationship.id, name="Planner Agent").first()

        # if planner doesn't exist, create a new one
        if not planner_agent:
            planner_agent = PlannerAgent(sender_voter_relationship_id=sender_voter_relationship.id)
            db.session.add(planner_agent)
            db.session.commit()
            # get the hydrated planner agent
            planner_agent = Agent.query.filter_by(sender_voter_relationship_id=sender_voter_relationship.id, name="Planner Agent").first()

        planner_prompt = f"Start a text conversation with the voter to accomplish this goal: {interaction.campaign.campaign_goal}. The associated interaction id is {interaction.id}."
        planner_agent.send_prompt({
            "content": planner_prompt
        })

def get_interaction(data):
    #Check if there is a sender id. If there is return all interactions for that sender
    if 'sender_id' in data.keys():
        sender_id = data['sender_id']
        interaction_type = interaction.interaction_type

        system_prompt = INTERACTION_TYPES[interaction_type].system_initialization_method(interaction)

        user_number = interaction.voter.voter_phone_number
        sender_number = interaction.select_phone_number()

        # Pre-create the first response
        interaction.conversation = initialize_conversation(system_prompt)
        initial_statement = get_llm_response_to_conversation(interaction.conversation)

        # check if the initial statement is the same as the system prompt, if so, try again to get a different response
        while initial_statement['content'] == system_prompt:
            print("Initial statement is the same as the system prompt, trying again")
            interaction.conversation = initialize_conversation(system_prompt)
            initial_statement = get_llm_response_to_conversation(interaction.conversation)

        interaction.conversation.append(initial_statement)

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

def update_interaction(data):
    print("Updating interaction")
    interaction_id = data['interaction_id']
    interaction = Interaction.query.get(interaction_id)
    if not interaction:
        return jsonify({'error': 'Interaction does not exist', 'status_code': 404}), 404

    interaction_status = data['interaction_status']
    interaction.interaction_status = interaction_status

    db.session.add(interaction)
    db.session.commit()

    return jsonify({'interaction': interaction.to_dict(), 'status_code': 200}), 200
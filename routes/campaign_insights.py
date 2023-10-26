import json
from flask import Blueprint, jsonify, request, current_app
from models.sender import Campaign
from models.interaction import Interaction, InteractionStatus
from prompts.interaction_evaluation_agent import get_conversation_evaluation_system_prompt
from prompts.campaign_insights_agent import get_campaign_summary_system_prompt
from tools.utility import get_llm_response_to_conversation , initialize_conversation
from context.database import db
from context.sockets import socketio
import threading

# blueprint definition
campaign_insights_bp = Blueprint('campaign', __name__)

@campaign_insights_bp.route('/campaign/insights', methods=['PUT'])
def campaign_insights():
    # check if the content type of the request is json
    if not request.is_json:
        return jsonify({'error': 'Request body must be JSON', 'status_code': 400}), 400
    
    json = request.json
    # look for the campaign id in the request body
    campaign_id = json.get('campaign_id', None)

    if not campaign_id:
        return jsonify({'error': 'campaign_id is required', 'status_code': 400}), 400
    
    # check if the campaign exists
    campaign = Campaign.query.filter_by(id=campaign_id).first()
    if not campaign:
        return jsonify({'error': 'Campaign does not exist', 'status_code': 404}), 404
    
    if 'refresh_funnel' in json.keys():
        # Get a count of all interactions in this campaign with a status of InteractionStatus.SENT or greater
        socketio.emit('message', {'campaign_id': campaign_id, 'message': 'Refreshing funnel'}, room=f'subscribe_funnel_refresh_{campaign_id}')
        campaign.interactions_sent = Interaction.query.filter(Interaction.campaign_id == campaign_id, Interaction.interaction_status >= InteractionStatus.SENT).count()
        campaign.interactions_delivered = Interaction.query.filter(Interaction.campaign_id == campaign_id, Interaction.interaction_status >= InteractionStatus.DELIVERED).count()
        campaign.interactions_responded = Interaction.query.filter(Interaction.campaign_id == campaign_id, Interaction.interaction_status >= InteractionStatus.RESPONDED).count()
        campaign.interactions_converted = Interaction.query.filter(Interaction.campaign_id == campaign_id, Interaction.interaction_status >= InteractionStatus.CONVERTED).count()
        socketio.emit('funnel_refreshed', {'campaign_id': campaign_id}, room=f'subscribe_funnel_refresh_{campaign_id}')

    if 'refresh_campaign_insights' in json.keys():
        print("Starting campaign summary")
        thread = threading.Thread(target=summarize_campaign, args=[campaign, current_app._get_current_object()])
        thread.start()

    if 'refresh_interaction_evaluations' in json.keys():
        if 'interaction_id' in json.keys():
            # Get the interaction
            interaction_id = json['interaction_id']
            # get the interaction with the correct ID and the campaign_id from the request
            interaction = Interaction.query.filter_by(id=interaction_id, campaign_id=campaign_id).first()
            if not interaction:
                return jsonify({'error': 'Interaction does not exist in this campaign', 'status_code': 404}), 404
            thread = threading.Thread(target=evaluate_interaction, args=[interaction, current_app._get_current_object()])
            thread.start()
        else:
            for interaction in campaign.interactions:
                print("Checking interaction for update")
                if interaction.interaction_status >= InteractionStatus.SENT:
                    print("Interaction needs to be updated")
                    thread = threading.Thread(target=evaluate_interaction, args=[interaction, current_app._get_current_object()])
                    thread.start()

    db.session.add(campaign)
    db.session.commit()

    return jsonify({'status': 'success', 'status_code': 200}), 200

def summarize_campaign(campaign: Campaign, app):
    with app.app_context():
        print(f"Starting summary for campaign {campaign.id}")
        system_prompt = get_campaign_summary_system_prompt(campaign)

        summary = initialize_conversation(system_prompt)

        json_summary = {}

        retry_count = 0

        max_retries = 50

        while not json_summary and retry_count <= max_retries:

            llm_response = get_llm_response_to_conversation(summary)

            try:
                json_summary = json.loads(llm_response['content'])
            except json.decoder.JSONDecodeError as error:
                print(f"Error decoding JSON from LLM response: {error}")
                # try again
                retry_count += 1
                continue

        if not json_summary:
            socketio.emit('campaign_insight_error', {'campaign_id': campaign.id, 'error': 'Error decoding JSON from LLM response'}, room=f'subscribe_campaign_insight_refresh_{campaign.id}')
            return

        print(f"Summary: {json_summary}")

        campaign.campaign_manager_summary = json_summary['campaign_manager_summary']
        campaign.communications_director_summary = json_summary['communications_director_summary']
        campaign.field_director_summary = json_summary['field_director_summary']
        campaign.policy_insights = json_summary['policy_insights']

        db.session.add(campaign)
        db.session.commit()

        socketio.emit('campaign_insight_refreshed', {'campaign_id': campaign.id}, room=f'subscribe_campaign_insight_refresh_{campaign.id}')

def evaluate_interaction(interaction: Interaction, app):
    print(f"Starting evaluation for interaction {interaction.id}")
    with app.app_context():

        interaction = Interaction.query.get(interaction.id)

        # emit a socket event to the campaign insights page to update the UI
        socketio.emit('beginning_evaluation', {'interaction_id': interaction.id}, room=f'subscribe_interaction_evaluation_{interaction.id}')

        # Get the system prompt for evaluating this interaction
        system_prompt = get_conversation_evaluation_system_prompt(interaction.conversation)

        evaluation = initialize_conversation(system_prompt)


        json_evaluation = {}


        retry_count = 0
        max_retries = 50

        while not json_evaluation and retry_count <= max_retries:
            try:
                socketio.emit('message', {'interaction_id': interaction.id, 'message': f"Calling LLM with conversation: {evaluation}"}, room=f'subscribe_interaction_evaluation_{interaction.id}')
                llm_response = get_llm_response_to_conversation(evaluation)
                socketio.emit('message', {'interaction_id': interaction.id, 'message': f"LLM response for evaluation: {llm_response}"}, room=f'subscribe_interaction_evaluation_{interaction.id}')

                # print(f"LLM response for evaluation: {llm_response}")

                # get the json object at llm_response['content']

                json_evaluation = json.loads(llm_response['content'])
            except json.decoder.JSONDecodeError as error:
                print(f"Error decoding JSON from LLM response: {error}")
                # try again
                retry_count += 1
                continue

        if not json_evaluation:

            socketio.emit('interaction_evaluation_error', {'interaction_id': interaction.id, 'error': 'Error decoding JSON from LLM response'}, room=f'subscribe_interaction_evaluation_{interaction.id}')
            return
        
        print(f"Evaluation: {json_evaluation}")

        # set the interaction fields from the json object

        # check if the goal achieved contains the text "True" then convert to boolean

        goal_achieved = json_evaluation['goal_achieved']

        #check if goal achieved is a boolean
        if isinstance(goal_achieved, bool):
            interaction.goal_achieved = goal_achieved
        else:
            interaction.goal_achieved = "True" in json_evaluation['goal_achieved']
        interaction.rating_explanation = json_evaluation['rating_explanation']
        interaction.rating = json_evaluation['rating']
        interaction.campaign_relevance_score = json_evaluation['campaign_relevance_score']
        interaction.campaign_relevance_explanation = json_evaluation['campaign_relevance_explanation']
        interaction.campaign_relevance_summary = json_evaluation['campaign_relevance_summary']
        interaction.insights_about_issues = json_evaluation['insights_about_issues']
        interaction.insights_about_voter = json_evaluation['insights_about_voter']

        if interaction.goal_achieved:
            interaction.interaction_status = InteractionStatus.CONVERTED

        db.session.add(interaction)
        db.session.commit()

        # emit a socket event to the campaign insights page to update the UI
        socketio.emit('interaction_evaluated', {'interaction_id': interaction.id}, room=f'subscribe_interaction_evaluation_{interaction.id}')


        
import json
from flask import Blueprint, jsonify, request, current_app
from models.sender import Campaign
from models.interaction import Interaction, InteractionStatus
from prompts.interaction_evaluation_agent import get_conversation_evaluation_system_prompt
from tools.utility import get_llm_response_to_conversation
from context.database import db
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
        campaign.interactions_sent = Interaction.query.filter(Interaction.campaign_id == campaign_id, Interaction.interaction_status >= InteractionStatus.SENT).count()
        campaign.interactions_delivered = Interaction.query.filter(Interaction.campaign_id == campaign_id, Interaction.interaction_status >= InteractionStatus.DELIVERED).count()
        campaign.interactions_responded = Interaction.query.filter(Interaction.campaign_id == campaign_id, Interaction.interaction_status >= InteractionStatus.RESPONDED).count()
        campaign.interactions_converted = Interaction.query.filter(Interaction.campaign_id == campaign_id, Interaction.interaction_status >= InteractionStatus.CONVERTED).count()

    if 'refresh_campaign_insights' in json.keys():
        campaign.campaign_manager_summary = 'This is a summary of the campaign for a campaign manager'
        campaign.communications_director_summary = 'This is a summary of the campaign for a communications director'
        campaign.field_director_summary = 'This is a summary of the campaign for a field director'

    if 'refresh_interaction_evaluations' in json.keys():
        for interaction in campaign.interactions:
            print("Checking interaction for update")
            if interaction.interaction_status >= InteractionStatus.SENT:
                print("Interaction needs to be updated")
                thread = threading.Thread(target=evaluate_interaction, args=[interaction, current_app._get_current_object()])
                thread.start()

    db.session.add(campaign)
    db.session.commit()

    return jsonify({'status': 'success', 'status_code': 200}), 200

def evaluate_interaction(interaction: Interaction, app):
    print(f"Starting evaluation for interaction {interaction.id}")
    with app.app_context():
        # Get the system prompt for evaluating this interaction
        system_prompt = get_conversation_evaluation_system_prompt(interaction.conversation)

        evaluation = [{
            "role": "system",
            "content": system_prompt
        }]

        llm_response = get_llm_response_to_conversation(evaluation)

        # print(f"LLM response for evaluation: {llm_response}")

        # get the json object at llm_response['content']
        json_evaluation = json.loads(llm_response['content'])
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


        
from flask import Blueprint, jsonify, request
from models.models import Campaign
from context.database import db
import math
import random

# blueprint definition
campaign_insights_bp = Blueprint('campaign', __name__)

@campaign_insights_bp.route('/campaign/insights', methods=['POST'])
def campaign_insights():
    # check if the content type of the request is json
    if not request.is_json:
        return jsonify({'error': 'Request body must be JSON', 'status_code': 400}), 400
    # look for the campaign id in the request body
    campaign_id = request.json.get('campaign_id', None)

    if not campaign_id:
        return jsonify({'error': 'campaign_id is required', 'status_code': 400}), 400
    
    # check if the campaign exists
    campaign = Campaign.query.filter_by(id=campaign_id).first()
    if not campaign:
        return jsonify({'error': 'Campaign does not exist', 'status_code': 404}), 404
    
    if 'refresh_funnel' in request.keys():
        campaign.interactions_sent = 100
        campaign.interactions_delivered = 90
        campaign.interactions_responded = 50
        campaign.interactions_converted = 20

    if 'refresh_campaign_insights' in request.keys():
        campaign.campaign_manager_summary = 'This is a summary of the campaign for a campaign manager'
        campaign.communications_director_summary = 'This is a summary of the campaign for a communications director'
        campaign.field_director_summary = 'This is a summary of the campaign for a field director'

    if 'refresh_interaction_evaluations' in request.keys():
        '''
        Loop through the interactions in this campaign and update their evaluations and insights

        # Evaluation of the interaction
        goal_achieved = db.Column(db.Boolean())
        rating_explanation = db.Column(db.Text())
        rating = db.Column(db.Integer())
        campaign_relevance_score = db.Column(db.Integer()) # how interesting this interaction would be for the sender to know about
        campaign_relevance_explanation = db.Column(db.Text())
        campaign_relevance_summary = db.Column(db.Text())

        #Summary of interaction to aggregate useful takeaways
        insights_about_issues = db.Column(db.Text())
        insights_about_recipient = db.Column(db.Text())
        '''
        for interaction in campaign.interactions:
            interaction.goal_achieved = True
            interaction.rating_explanation = 'This interaction was very successful'
            interaction.rating = math.floor(random.random() * 10)
            interaction.campaign_relevance_score = math.floor(random.random() * 100)
            interaction.campaign_relevance_explanation = 'This interaction is very relevant to the campaign'
            interaction.campaign_relevance_summary = 'This interaction is very relevant to the campaign because it has intersting and unique insights about the audience'
            interaction.insights_about_issues = 'This conversation discussed gun control and the environment. The gun control is too strict and the environment is overblown'
            interaction.insights_about_recipient = 'This recipient cares about the 2nd amendment and is a hunter'
            db.session.add(interaction)

    db.session.add(campaign)
    db.session.commit()
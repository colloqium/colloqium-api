from flask import Blueprint, jsonify, request, current_app
from models.sender import Campaign
from models.interaction import Interaction, InteractionStatus
from context.database import db
from context.sockets import socketio
from tasks.campaign_analysis import summarize_campaign, evaluate_interaction

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
        summarize_campaign.apply_async(args=[campaign.id])

    if 'refresh_interaction_evaluations' in json.keys():
        if 'interaction_id' in json.keys():
            # Get the interaction
            interaction_id = json['interaction_id']
            # get the interaction with the correct ID and the campaign_id from the request
            interaction = Interaction.query.filter_by(id=interaction_id, campaign_id=campaign_id).first()
            if not interaction:
                return jsonify({'error': 'Interaction does not exist in this campaign', 'status_code': 404}), 404
            evaluate_interaction.apply_async(args=[interaction.id])
        else:
            for interaction in campaign.interactions:
                print("Checking interaction for update")
                if interaction.interaction_status >= InteractionStatus.SENT:
                    print("Interaction needs to be updated")
                    evaluate_interaction.apply_async(args=[interaction.id])

    db.session.add(campaign)
    db.session.commit()

    return jsonify({'status': 'success', 'status_code': 200}), 200 
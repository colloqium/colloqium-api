from context.celery import celery_client
from tasks.base_task import BaseTaskWithDB
from models.interaction import Interaction
from models.sender import Campaign
from flask import jsonify
from tasks.initialize_interaction import initialize_interaction
from context.database import db
from logs.logger import logger
from models.interaction import InteractionStatus
from models.interaction_types import INTERACTION_TYPES
from models.voter import Voter

@celery_client.task(bind=True, base=BaseTaskWithDB, max_retries=10, default_retry_delay=30)
def create_interactions_from_campaign(self, campaign_id: int, interaction_type: str):
    with self.session_scope():
        print("Creating interaction for campaign")
        campaign = Campaign.query.get(campaign_id)
        audiences = campaign.audiences

        if not audiences:
            print("Campaign does not have an audience")
            return jsonify({'error': 'Campaign does not have an audience', 'status_code': 404}), 404


        print("Campaign has an audience")
        for audience in audiences:
            voters = audience.voters
            for voter in voters:
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

                initialize_interaction.apply_async(args=[interaction.id])

def build_interaction(voter: Voter, interaction_type: str, campaign: Campaign = None) -> Interaction:
    if not voter:
        print("Voter does not exist for interaction")
        return jsonify({'error': 'voter does not exist', 'status_code': 404}), 404
    
    # check if the interaction types is in the keys of INTERACTION_TYPES
    if interaction_type not in INTERACTION_TYPES.keys():
        logger.debug("Invalid interaction type")
        logger.debug(f"Interaction type keys: {INTERACTION_TYPES.keys()}")
        logger.debug(f"Interaction type: {interaction_type}")
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
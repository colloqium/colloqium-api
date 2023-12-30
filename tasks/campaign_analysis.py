import json
from models.sender import Campaign
from models.interaction import Interaction, InteractionStatus, SenderVoterRelationship
from models.ai_agents.agent import Agent
from models.ai_agents.voter_analysis_agent import VoterAnalysisAgent
from prompts.interaction_evaluation_agent import get_conversation_evaluation_system_prompt
from prompts.campaign_insights_agent import get_campaign_summary_system_prompt
from tools.utility import get_llm_response_to_conversation , initialize_conversation
from context.database import db
from context.sockets import socketio
from context.celery import celery_client
from context.analytics import analytics, EVENT_OPTIONS
from tasks.base_task import BaseTaskWithDB


@celery_client.task(bind=True, base=BaseTaskWithDB, max_retries=10, default_retry_delay=30)  # bind=True to access self, max_retries and default_retry_delay are optional
def summarize_campaign(self, campaignId: int):
    with self.session_scope():

        campaign = Campaign.query.get(campaignId)

        if not campaign:
            print("Campaign does not exist")
            return

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
        db.session.remove()

        socketio.emit('campaign_insight_refreshed', {'campaign_id': campaign.id}, room=f'subscribe_campaign_insight_refresh_{campaign.id}')

@celery_client.task(bind=True, base=BaseTaskWithDB, max_retries=5, default_retry_delay=30)  # bind=True to access self, max_retries and default_retry_delay are optional
def evaluate_interaction(self, interactionId: int):

    with self.session_scope():
        interaction = Interaction.query.get(interactionId)

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

        update_voter_profile.delay(interaction.id)


@celery_client.task(bind=True, base=BaseTaskWithDB, max_retries=5, default_retry_delay=30)  # bind=True to access self, max_retries and default_retry_delay are optional
def update_voter_profile(self, interactionId: int):

    with self.session_scope():
        interaction = Interaction.query.get(interactionId)

        voter = interaction.voter

        voter_profile = voter.voter_profile

        sender_voter_relationship = SenderVoterRelationship.query.filter_by(sender_id=interaction.sender_id, voter_id=interaction.voter_id).first()

        if not sender_voter_relationship:
            sender_voter_relationship = SenderVoterRelationship(sender_id=interaction.sender_id, voter_id=interaction.voter_id)
            db.session.add(sender_voter_relationship)
            db.session.commit()
            # get the hydrated sender_voter_relationship
            sender_voter_relationship = SenderVoterRelationship.query.filter_by(sender_id=interaction.sender_id, voter_id=interaction.voter_id).first()

        voter_analysis_agent = Agent.query.filter_by(sender_voter_relationship_id=sender_voter_relationship.id, name="voter_analysis_agent").first()

        if not voter_analysis_agent:
            voter_analysis_agent = VoterAnalysisAgent(voter_id = voter.id, latest_interaction_id = interaction.id)

        # create a prompt for the voter analysis agent to review the voter profile, the latest interaction, and update the voter profile so that we can tailor or contact to the voter and be more responsive to their needs
        voter_analyst_request_prompt = '''
            Please gives us an updated voter profile for {voter_name}.

            Current Voter Profile:
            {voter_profile}

            Last Interaction:
            {last_interaction}

            Remember to return your analysis as a complete JSON object. Your result will fully overwrite the current voter profile, so please include all relevant information.

        '''

        relevant_interaction_object = {
            # get the conversation without the first message because we don't care about the system message
            "conversation": interaction.conversation[1:],
            "interaction_goal": interaction.interaction_goal,
            "goal_achieved": interaction.goal_achieved,
            "rating_explanation": interaction.rating_explanation,
            "rating": interaction.rating,
            "campaign_relevance_score": interaction.campaign_relevance_score,
            "campaign_relevance_explanation": interaction.campaign_relevance_explanation,
            "campaign_relevance_summary": interaction.campaign_relevance_summary,
            "insights_about_issues": interaction.insights_about_issues,
            "insights_about_voter": interaction.insights_about_voter
        }

        voter_analyst_request_prompt = voter_analyst_request_prompt.format(
            voter_name = voter.voter_name,
            voter_profile = voter_profile.to_dict(),
            last_interaction = relevant_interaction_object
        )

        voter_analysis_agent.send_prompt({
            "content": voter_analyst_request_prompt
        })

        db.session.add(voter_analysis_agent)

        # update voter profile with the result from the voter analysis agent
        analysis_json = voter_analysis_agent.last_message_as_json()
        
        voter_profile.interests = analysis_json['interests']
        voter_profile.policy_preferences = analysis_json['policy_preferences']
        voter_profile.background = analysis_json['background']
        voter_profile.last_interaction = analysis_json['last_interaction']
        voter_profile.preferred_contact_method = analysis_json['preferred_contact_method']

        db.session.add(voter_profile)
        db.session.commit()

        analytics.track(interaction.voter.id, EVENT_OPTIONS.voter_analyzed, {
            'sender_id': interaction.sender.id,
            'campaign_id': interaction.campaign.id,
            'interaction_id': interaction.id,
            'voter_profile': voter_profile.to_dict(),
        })


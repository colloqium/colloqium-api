import json
from models.sender import Campaign
from models.interaction import Interaction, InteractionStatus
from prompts.interaction_evaluation_agent import get_conversation_evaluation_system_prompt
from prompts.campaign_insights_agent import get_campaign_summary_system_prompt
from tools.utility import get_llm_response_to_conversation , initialize_conversation
from context.database import db
from context.sockets import socketio
from context.celery import celery_client
from sqlalchemy.exc import OperationalError
from tools.db_utility import check_db_connection
from celery.exceptions import MaxRetriesExceededError

@celery_client.task(bind=True, max_retries=10, default_retry_delay=30)  # bind=True to access self, max_retries and default_retry_delay are optional
def summarize_campaign(self, campaignId: int):
    from context.app import create_app # late import 
    app = create_app()
    try:
        with app.app_context():
            if not check_db_connection(db):
                print("Database connection failed")
                # retry in 30 seconds
                self.retry()

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

            socketio.emit('campaign_insight_refreshed', {'campaign_id': campaign.id}, room=f'subscribe_campaign_insight_refresh_{campaign.id}')
    except OperationalError as e:
        try:
            self.retry(exc=e) # retry the task
        except MaxRetriesExceededError:
            print("Max retries exceeded, aborting task")
        



@celery_client.task(bind=True, max_retries=5, default_retry_delay=30)  # bind=True to access self, max_retries and default_retry_delay are optional
def evaluate_interaction(self, interactionId: int):
    from context.app import create_app # late import 
    app = create_app()
    try:
        with app.app_context():
            try:
                if not check_db_connection(db):
                    print("Database connection failed")
                    # retry in 30 seconds
                    self.retry()
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
            finally:
                db.session.close_all()
    except OperationalError as e:
        try:
            self.retry(exc=e) # retry the task
        except MaxRetriesExceededError:
            print("Max retries exceeded, aborting task")
# import Flask and other libraries
from models.interaction import Interaction, SenderVoterRelationship
from models.ai_agents.planning_agent import PlanningAgent
from models.ai_agents.agent import Agent
from context.database import db
from context.celery import celery_client
from celery.exceptions import MaxRetriesExceededError
from sqlalchemy.exc import OperationalError
from tools.db_utility import check_db_connection

# Creates a new interaction with a voter and the first system message in the conversation. Does not send the message.
@celery_client.task(bind=True, max_retries=10, default_retry_delay=30)  # bind=True to access self, max_retries and default_retry_delay are optional
def initialize_interaction(self, interaction_id):
    from context.app import create_app # late import 
    app = create_app()
    try:
        with app.app_context():
            try:
                if not check_db_connection(db):
                    print("Database connection failed")
                    # retry in 30 seconds
                    self.retry()

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

                # look for an agent with the name planning_agent in the sender_voter_relationship
                planning_agent = Agent.query.filter_by(sender_voter_relationship_id=sender_voter_relationship.id, name="planning_agent").first()

                # if planner doesn't exist, create a new one
                if not planning_agent:
                    planning_agent = PlanningAgent(sender_voter_relationship_id=sender_voter_relationship.id)
                    db.session.add(planning_agent)
                    db.session.commit()
                    # get the hydrated planner agent
                    planning_agent = Agent.query.filter_by(sender_voter_relationship_id=sender_voter_relationship.id, name="planning_agent").first()

                planner_prompt = f"Start a text conversation with the voter to accomplish this goal: {interaction.campaign.campaign_goal}. The associated interaction id is {interaction.id}."
                planning_agent.send_prompt({
                    "content": planner_prompt
                })
            finally:
                db.session.close_all()
    except OperationalError as e:
        try:
            self.retry(exc=e) # retry the task
        except MaxRetriesExceededError:
            print("Max retries exceeded, aborting task")

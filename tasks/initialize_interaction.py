# import Flask and other libraries
from models.interaction import Interaction, SenderVoterRelationship
from models.interaction_types import INTERACTION_TYPES
from models.ai_agents.planning_agent import PlanningAgent
from models.ai_agents.agent import Agent
from context.database import db
from context.celery import celery_client
from tasks.base_task import BaseTaskWithDB

# Creates a new interaction with a voter and the first system message in the conversation. Does not send the message.
@celery_client.task(bind=True, base=BaseTaskWithDB, max_retries=10, default_retry_delay=30)  # bind=True to access self, max_retries and default_retry_delay are optional
def initialize_interaction(self, interaction_id):
    with self.session_scope():
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


        planner_prompt = "Wait for instructions from the campaign manager."

        print(f"Interaction Type Of Interaction: {interaction.interaction_type}")
        print(f"Text message from Interaction Types enum: {INTERACTION_TYPES['text_message']}")
        print(f"Robo call from Interaction Types enum: {INTERACTION_TYPES['robo_call']}")

        print(f"Check if interaction type is text message: {interaction.interaction_type == INTERACTION_TYPES['text_message']}")
        print(f"Check if interaction type is robo call: {interaction.interaction_type == INTERACTION_TYPES['robo_call']}")
        
        
        #switch on interaction type
        if interaction.interaction_type == INTERACTION_TYPES["text_message"].name:
            planner_prompt = f"Start a text conversation with the voter to accomplish this goal: {interaction.campaign.campaign_goal}. The associated interaction id is {interaction.id}."
        elif interaction.interaction_type == INTERACTION_TYPES["robo_call"].name: 
            planner_prompt = f"Send a robocall to the voter to accomplish this goal: {interaction.campaign.campaign_goal}. The associated interaction id is {interaction.id}."
        
        planning_agent.send_prompt({
            "content": planner_prompt
        })

        db.session.remove()

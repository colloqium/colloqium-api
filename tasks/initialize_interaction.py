# import Flask and other libraries
from models.interaction import Interaction, SenderVoterRelationship
from models.interaction_types import INTERACTION_TYPES
from models.ai_agents.planning_agent import PlanningAgent
from models.ai_agents.texting_agent import TextingAgent
from models.ai_agents.robo_caller_agent import RoboCallerAgent
from models.ai_agents.email_agent import EmailAgent
from models.ai_agents.agent import Agent
from models.ai_agents.campaign_message_agent import CampaignMessageAgent
from context.database import db
from context.celery import celery_client
from tasks.base_task import BaseTaskWithDB
from redis import Redis
from redlock import RedLock
import os

# Initialize Redis client and Redlock
redis_client = Redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379'))
dlm = RedLock("campaign_initial_message_")

# TODO: Switch this to populate with the fist message from the campaign rather than generating one from the LLM
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

        print(f"Interaction Type Of Interaction: {interaction.interaction_type}")
        print(f"Type of interaction.interaction_type: {type(interaction.interaction_type)}")
        print(f"Text message from Interaction Types enum: {INTERACTION_TYPES['text_message']}")
        print(f"Type of INTERACTION_TYPES['text_message']: {type(INTERACTION_TYPES['text_message'])}")

        # If interaction.interaction_type is a string, try converting INTERACTION_TYPES to string
        if isinstance(interaction.interaction_type, str):
            print(f"Check if interaction type is text message: {interaction.interaction_type == str(INTERACTION_TYPES['text_message'])}")
        else:
            print(f"Check if interaction type is text message: {interaction.interaction_type == INTERACTION_TYPES['text_message']}")

        print(f"Robo call from Interaction Types enum: {INTERACTION_TYPES['robo_call']}")
        print(f"Email from Interaction Types enum: {INTERACTION_TYPES['email']}")

        print(f"Check if interaction type is robo call: {interaction.interaction_type == INTERACTION_TYPES['robo_call']}")
        print(f"Check if interaction type is email: {interaction.interaction_type == INTERACTION_TYPES['email']}")

        # check if an initial message for this campaign already exists
        if interaction.campaign.initial_message:
            pass
        else:
            # Try to acquire a lock for this campaign
            lock = dlm.acquire()
            if lock:
                try:
                    # Double-check if the initial message was created while waiting for the lock
                    db.session.refresh(interaction.campaign)
                    if not interaction.campaign.initial_message:
                        # generate a new initial message
                        campaign_agent = CampaignMessageAgent(interaction.campaign.id)
                        initial_message = campaign_agent.send_prompt({
                            "content": "Generate an initial message for the campaign."
                        })
                        print(f"Initial message: {initial_message}")
                        interaction.campaign.initial_message = initial_message["llm_response"]["content"]
                        db.session.add(interaction.campaign)
                        db.session.commit()
                finally:
                    dlm.release()
            else:
                # If we couldn't acquire the lock, wait and retry
                self.retry(countdown=5)

        agent = None

        #if text create a texting agent
        if interaction.interaction_type == str(INTERACTION_TYPES["text_message"]):
            agent = TextingAgent(interaction.id)
            print("Created a texting agent")
        elif interaction.interaction_type == str(INTERACTION_TYPES["robo_call"]):
            agent = RoboCallerAgent(interaction.id)
            print("Created a robo caller agent")
        elif interaction.interaction_type == str(INTERACTION_TYPES["email"]):
            agent = EmailAgent(interaction.id)
            print("Created an email agent")

        print(f"Agent after creation: {agent}")
        print(f"Agent type: {type(agent)}")
        db.session.add(agent)
        db.session.commit()

        db.session.remove()
# import Flask and other libraries
from models.interaction import Interaction, SenderVoterRelationship
from models.interaction_types import INTERACTION_TYPES
from models.sender import Campaign, Sender
from models.ai_agents.planning_agent import PlanningAgent
from models.ai_agents.texting_agent import TextingAgent
from models.ai_agents.robo_caller_agent import RoboCallerAgent
from models.ai_agents.email_agent import EmailAgent
from models.ai_agents.agent import Agent
from models.ai_agents.campaign_message_agent import CampaignMessageAgent
from context.database import db
from context.celery import celery_client
from tasks.base_task import BaseTaskWithDB
from tools.vector_store_utility import get_vector_store_results
from redis import Redis
from redlock import RedLock
import os

# Initialize Redis client and Redlock
redis_client = Redis.from_url(os.getenv('REDIS_URL'))
dlm = RedLock(
                resource = "campaign_initial_message_",
                connection_details=[redis_client]
            )

# TODO: Switch this to populate with the fist message from the campaign rather than generating one from the LLM
# Creates a new interaction with a voter and the first system message in the conversation. Does not send the message.
@celery_client.task(bind=True, base=BaseTaskWithDB, max_retries=1, default_retry_delay=30)  # bind=True to access self, max_retries and default_retry_delay are optional
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
                        print("Generating a new initial message")
                        # generate a new initial message
                        campaign_agent = CampaignMessageAgent(interaction.campaign.id)
                        initial_message = campaign_agent.send_prompt({
                            "content": "Generate an initial message for the campaign."
                        })
                        print(f"Initial message: {initial_message}")
                        interaction.campaign.initial_message = initial_message["llm_response"]["content"]

                        # generate key examples
                        key_examples = generate_key_examples(interaction.campaign, interaction.sender)
                        print(f"Key examples: {key_examples}")
                        interaction.campaign.campaign_key_examples = key_examples

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
        elif interaction.interaction_type == str(INTERACTION_TYPES["robo_call"]):
            agent = RoboCallerAgent(interaction.id)
        elif interaction.interaction_type == str(INTERACTION_TYPES["email"]):
            agent = EmailAgent(interaction.id)

        db.session.add(agent)
        db.session.commit()

        db.session.remove()

def generate_key_examples(campaign: Campaign, sender: Sender):
    # look in the vector store for a subset of example interactions based on the campaign prompt
    key_examples = get_vector_store_results(campaign.campaign_prompt, 2, 0.25, {'context': 'sender', 'id': sender.id})

    # get the key_examples["text"] from each example and remove the brackets
    key_examples = [example["text"] for example in key_examples]

    # remove all [ and { }] from the examples
    key_examples = [example.replace("[", "").replace("]", "").replace("{", "").replace("}", "") for example in key_examples]

    return key_examples
# import Flask and other libraries
from models.interaction import InteractionStatus
from models.ai_agents.agent import Agent
from models.ai_agents.planning_agent import PlanningAgent
from models.interaction import SenderVoterRelationship
# from logs.logger import logging
from context.database import db
from context.analytics import analytics, EVENT_OPTIONS
from tools.ai_functions.send_message import SendMessage
from logs.logger import logger
from sqlalchemy.orm.attributes import flag_modified
from context.celery import celery_client
from models.interaction import InteractionStatus, Interaction
from tasks.base_task import BaseTaskWithDB


@celery_client.task(bind=True, base=BaseTaskWithDB, max_retries=10, default_retry_delay=30)  # bind=True to access self, max_retries and default_retry_delay are optional
def process_inbound_message(self, interaction_id, message_body, sender_phone_number):
    with self.session_scope():
        interaction = Interaction.query.filter_by(id=interaction_id).first()
        voter = interaction.voter
        sender = interaction.sender

        if not interaction:
            print("Interaction not found")
            return
        
        interaction.interaction_status = InteractionStatus.RESPONDED

        # Now you can add the new message to the conversation
        logger.info(f"Recieved message message body: {message_body}")
        # print(f"Recieved message body: {message_body}")
        analytics.track(voter.id, EVENT_OPTIONS.recieved, {
            'interaction_id': interaction.id,
            'voter_name': voter.voter_name,
            'voter_phone_number': voter.voter_phone_number,
            'sender_name': sender.sender_name,
            'sender_phone_number': sender_phone_number,
            'interaction_type': interaction.interaction_type,
            'message': message_body,
        })

        # get the texting agent with the interaction in it's interactions list
        texting_agent = Agent.query.filter(Agent.interactions.any(id=interaction.id)).first()
        
        if not texting_agent:
            logger.error("No agent attached")
            print("No agent attached")
            return
        
        # send the message to the planning agent
        texting_agent.send_prompt({
            "content": f"{message_body}",
        })

        interaction.conversation = texting_agent.conversation_history.copy()

        flag_modified(interaction, "conversation")
        db.session.add(interaction)
        db.session.commit()

        sender_voter_relationship = SenderVoterRelationship.query.filter_by(sender_id=sender.id, voter_id=voter.id).first()

        # look for an agent with the name planning_agent in the sender_voter_relationship
        planning_agent = Agent.query.filter_by(sender_voter_relationship_id=sender_voter_relationship.id, name="planning_agent").first()

        # if planner doesn't exist, create a new one
        if not planning_agent:
            planning_agent = PlanningAgent(sender_voter_relationship_id=sender_voter_relationship.id)
            db.session.add(planning_agent)
            db.session.commit()
            # get the hydrated planner agent
            planning_agent = Agent.query.filter_by(sender_voter_relationship_id=sender_voter_relationship.id, name="planning_agent").first()

        
        # check if the last element in the texting agent is a function, if so do not send a message
        if "function_call" in texting_agent.conversation_history[-1].keys():
            print("Last message is a function call")
            return
        
        if "ended because" in texting_agent.conversation_history[-1].get('content'):
            print("Conversation ended")
            return

        send_message = SendMessage()

        kwargs = {
            "campaign_id": interaction.campaign_id,
            "voter_id": interaction.voter_id,
            "outbound_message": texting_agent.conversation_history[-1].get('content')
        }

        send_message.call(**kwargs)

        db.session.remove()
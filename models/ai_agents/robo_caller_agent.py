from models.ai_agents.agent import Agent
from models.interaction import SenderVoterRelationship
from models.interaction import Interaction, InteractionStatus
from context.database import db
from tools.utility import get_llm_response_to_conversation, initialize_conversation
from tools.vector_store_utility import get_vector_store_results
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate
from context.sockets import socketio
from context.analytics import analytics, EVENT_OPTIONS
import json
from logs.logger import logger

class RoboCallerAgent(Agent):
    __mapper_args__ = {
        'polymorphic_identity': 'robo_caller_agent'
    }
    
    def __init__(self, interaction_id: int):

        with db.session.no_autoflush:
            print(f"Creating a new RoboCallerAgent for interaction_id {interaction_id}")

            # get interaction
            interaction = Interaction.query.get(interaction_id)

            if interaction is None:
                raise Exception("Interaction not found")
            
            # get campaign
            campaign = interaction.campaign

            # get sender
            sender = interaction.sender

            # get voter
            voter = interaction.voter

            sender_voter_relationship = SenderVoterRelationship.query.filter_by(sender_id=sender.id, voter_id=voter.id).first()

            # look in the vector store for a subset of example interactions based on the campaign prompt
            key_examples = get_vector_store_results(campaign.campaign_prompt, 3, 0.25, {'context': 'sender', 'id': sender.id})

            # get the key_examples["text"] from each example and remove the brackets
            key_examples = [example["text"] for example in key_examples]

            # remove all [ and { }] from the examples
            key_examples = [example.replace("[", "").replace("]", "").replace("{", "").replace("}", "") for example in key_examples]

            prompt_template = '''
                Hi, you're going to be writing a concise and engaging script that sounds like a message from a knowledgeable and friendly campaign volunteer. The tone should be professional, informative, and personable.

                Key Elements to Include:

                Professional Greeting: Start with "Hello, this is <your_name>, reaching out from the {sender_name} campaign."
                Campaign Information: Include details about the campaign and how it connects with issues that might interest the voter.
                Personalized Invitation for Involvement: Offer a genuine invitation to get involved, related to "{campaign_goal}", and tailor it to the voter using "{voter_name}" for a personal touch.
                Appreciative Closing: Thank the listener for their time, and direct them to "{campaign_fallback}" for more information.


                The message will be successful if the recipient does {campaign_goal}

                You're instructions for this script:
                {campaign_prompt}
                
                
                Available information:

                Voter Name: {voter_name}
                Voter Profile:
                {voter_information}
                
                Campaign Name: {campaign_name}
                Campaign End Date: {campaign_end_date}
                
                Your Name: {sender_name}
                Sender Information: {sender_information}

                Example Interactions: {example_interactions}
                
                Campaign ID: {campaign_id}
                Voter ID: {voter_id}
                Sender ID: {sender_id}
                
                
                Tone and Approach:

                Tone: Approachable and respectful, with a slight personal touch without being overly familiar.
                Approach: Imagine you're an informed volunteer who is passionate about the campaign, speaking to a potential supporter with shared interests.
            '''

            system_prompt_template = SystemMessagePromptTemplate.from_template(prompt_template)

            chat_prompt_template = ChatPromptTemplate.from_messages([system_prompt_template])

            self.system_prompt = chat_prompt_template.format(
                voter_name = voter.voter_name,
                campaign_name = campaign.campaign_name,
                campaign_end_date = campaign.campaign_end_date,
                sender_name = sender.sender_name,
                voter_information = voter.voter_profile.to_dict(),
                campaign_prompt = campaign.campaign_prompt,
                sender_information = sender.sender_information,
                campaign_goal = campaign.campaign_goal,
                example_interactions = key_examples,
                campaign_id = campaign.id,
                voter_id = voter.id,
                sender_id = sender.id,
                campaign_fallback = sender.fallback_url
            )

            super().__init__(self.system_prompt, "robo_caller_agent", "Writes robo_call scripts", sender_voter_relationship.id)

            self.conversation_history = initialize_conversation(self.system_prompt)

            first_llm_response = get_llm_response_to_conversation(self.conversation_history)

            while first_llm_response['content'] == self.system_prompt:
                print("The llm did not return a response. Trying again.")
                first_llm_response = get_llm_response_to_conversation(self.conversation_history)

            self.conversation_history.append(first_llm_response)

            logger.info(f"Generated first response for robo-calling agent: {first_llm_response}")

            interaction.conversation = self.conversation_history
            interaction.interaction_status = InteractionStatus.INITIALIZED
 
            self.available_actions = json.dumps([])
            self.interactions = [interaction]
            
            db.session.add(self)
            db.session.add(interaction)

            # Send a message to all open WebSocket connections with a matching campaign_id
            socketio.emit('interaction_initialized', {'interaction_id': interaction.id, 'campaign_id': interaction.campaign_id}, room=f'subscribe_campaign_initialization_{interaction.campaign_id}')
            socketio.emit('interaction_initialized', {'interaction_id': interaction.id, 'sender_id': interaction.sender_id}, room=f'subscribe_sender_confirmation_{interaction.sender_id}')


            analytics.track(interaction.voter.id, EVENT_OPTIONS.initialized, {
                'sender_id': interaction.sender.id,
                'sender_phone_number': interaction.select_phone_number(),
                'interaction_type': interaction.interaction_type,
                'interaction_id': interaction.id
            })
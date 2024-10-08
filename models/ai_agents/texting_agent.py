from models.ai_agents.agent import Agent
from models.interaction import SenderVoterRelationship
from models.interaction import Interaction, InteractionStatus
from context.database import db
from tools.utility import get_llm_response_to_conversation, initialize_conversation
from tools.vector_store_utility import get_vector_store_results
from tools.ai_functions.alert_campaign_team import AlertCampaignTeam
from tools.ai_functions.end_conversation import EndConversation
from tools.ai_functions.get_candidate_information import GetCandidateInformation
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate
from context.sockets import socketio
from context.analytics import analytics, EVENT_OPTIONS
import json

class TextingAgent(Agent):
    __mapper_args__ = {
        'polymorphic_identity': 'texting_agent'
    }
    
    def __init__(self, interaction_id: int):

        with db.session.no_autoflush:
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


            key_examples = campaign.campaign_key_examples

            prompt_template = '''
                Hey there! You're helping to connect with {voter_name} on behalf of {sender_name}. The tone? Let's keep it friendly and straightforward—like chatting with a mature friend. Aim for 1-2 sentences; keep it short and sweet. If the conversation starts to fizzle or they're all out of questions, make sure to say "goodbye" to wrap it up.

                When you give your name, make sure to mention that you are an AI agent helping the campaign connect with voters so they know they are talking to an AI.

                Campaign Details:
                {campaign_prompt}

                What We're Trying to Achieve: 
                {campaign_goal}

                Campaign End Date:
                {campaign_end_date} (Note: that's election day for political races.)

                Sender Information:
                {sender_information} 

                Voter Information:
                {voter_information}

                Remember, always incorporate relevant voter information if it will help the conversation.

                Here is the type of information you may have about the candidate:
                {example_interactions}

                Don't Know the Answer? Point them here: {campaign_fallback}

                IDs You Might Need:
                Campaign ID: {campaign_id}
                Voter ID: {voter_id} 
                Sender ID: {sender_id}

                Output Format:
                Please provide your responses as plain text only, without any additional formatting, labels, or annotations. The text should be ready to send directly to the voter without any further modifications.

                Remember, these are text messages. Do not include any headers or additional context before the first message.

                Wait for a human go-ahead before sending the first message. After that, feel free to continue the conversation.
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
                campaign_fallback = sender.fallback_url,
                example_interactions = key_examples,
                campaign_id = campaign.id,
                voter_id = voter.id,
                sender_id = sender.id
            )

            super().__init__(self.system_prompt, "texting_agent", "Writes text messages", sender_voter_relationship.id)

            self.conversation_history = initialize_conversation(self.system_prompt)

            first_message = campaign.initial_message

            # Check if first_message is a dictionary and has a 'content' key
            if isinstance(first_message, dict) and 'content' in first_message:
                content = first_message['content']
            else:
                # If it's not a dictionary or doesn't have 'content', use it directly
                content = str(first_message)

            #break the voters name in to first and last name
            voter_first_name = interaction.voter.voter_name.split(" ")[0]

            # replace <VOTER_NAME> in the initial message with the voter's name
            content = content.replace("<VOTER_NAME>", voter_first_name)

            self.conversation_history.append({"role": "assistant", "content": content})

            interaction.conversation = self.conversation_history
            interaction.interaction_status = InteractionStatus.INITIALIZED
 
            self.available_actions = json.dumps([AlertCampaignTeam().to_dict(), EndConversation().to_dict(), GetCandidateInformation().to_dict()])
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
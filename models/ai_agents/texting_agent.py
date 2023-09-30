from models.ai_agents.agent import Agent
from models.interaction import SenderVoterRelationship
from models.sender import Sender, Campaign
from models.interaction import Interaction, InteractionStatus
from models.voter import Voter
from context.database import db
from tools.utility import get_llm_response_to_conversation, initialize_conversation
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate
from context.sockets import socketio
from context.analytics import analytics, EVENT_OPTIONS

class TextingAgent(Agent):
    def __init__(self, interaction_id: int):

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

        prompt_template = '''You are a helpful agent reaching out to {voter_name} on behalf of {sender_name} Keep your comments short, but welcoming. Please respond with 1 or 2 sentences and be brief. Your responses should be concise, informative, and engaging. If the voter is losing interest in the conversation or has no more questions, include "goodbye" in your response to mark the end of the communication.

                Follow these instructions when reaching out to the voter:
                {campaign_prompt}

                This campaign will be successful if you can accomplish the following goal:
                {campaign_goal}

                The campaign is going to end on {campaign_end_date}. For political races the end date is the election day.

                You know the following about the sender of the message:
                {sender_information}

                You know the following about the voter of the message:
                {voter_information}

                Here are some examples from the sender on how to respond to some questions:
                {example_interactions}

                If the voter asks you a question that you do not know the answer to, refer them to the following:
                {campaign_fallback}

                You are sending the voter a text message.

                Begin by with an engaging message that helps you accomplish your goal. Do not proactively reveal that you are an AI bot, but answer honestly when asked.
        '''

        system_prompt_template = SystemMessagePromptTemplate.from_template(prompt_template)

        chat_prompt_template = ChatPromptTemplate.from_messages([system_prompt_template])

        self.system_prompt = chat_prompt_template.format(
            voter_name = voter.voter_name,
            campaign_name = campaign.campaign_name,
            campaign_end_date = campaign.campaign_end_date,
            sender_name = sender.sender_name,
            voter_information = voter.voter_profile.interests,
            campaign_prompt = campaign.campaign_prompt,
            sender_information = sender.sender_information,
            campaign_goal = campaign.campaign_goal,
            campaign_fallback = sender.fallback_url,
            example_interactions = sender.example_interactions
        )

        super().__init__(self.system_prompt, "Texting Agent", "Writes text messages", sender_voter_relationship.id)

        self.conversation_history = initialize_conversation(self.system_prompt)

        first_llm_response = get_llm_response_to_conversation(self.conversation_history)

        while first_llm_response['content'] == self.system_prompt:
            print("The llm did not return a response. Trying again.")
            first_llm_response = get_llm_response_to_conversation(self.conversation_history)

        self.conversation_history.append(first_llm_response)

        interaction.conversation = self.conversation_history
        interaction.interaction_status = InteractionStatus.INITIALIZED

        db.session.add(self)
        db.session.add(interaction)
        db.session.commit()

        # Send a message to all open WebSocket connections with a matching campaign_id
        socketio.emit('interaction_initialized', {'interaction_id': interaction.id, 'campaign_id': interaction.campaign_id}, room=f'subscribe_campaign_initialization_{interaction.campaign_id}')
        socketio.emit('interaction_initialized', {'interaction_id': interaction.id, 'sender_id': interaction.sender_id}, room=f'subscribe_sender_confirmation_{interaction.sender_id}')


        analytics.track(interaction.voter.id, EVENT_OPTIONS.initialized, {
            'sender_id': interaction.sender.id,
            'sender_phone_number': interaction.select_phone_number(),
            'interaction_type': interaction.interaction_type,
            'interaction_id': interaction.id
        })


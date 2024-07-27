from models.sender import Sender, Campaign
from models.ai_agents.agent import Agent
from tools.utility import initialize_conversation, get_llm_response_to_conversation
from tools.vector_store_utility import get_vector_store_results
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate
import json
from context.database import db

class CampaignMessageAgent(Agent):
    __mapper_args__ = {
        'polymorphic_identity': 'campaign_message_agent'
    }

    def __init__(self, campaign_id: int):
        print(f"Creating a new CampaignMessageAgent for campaign_id {campaign_id}")

        # get campaign
        campaign = Campaign.query.get(campaign_id)

        # get sender
        sender = Sender.query.get(campaign.sender_id)

        # look in the vector store for a subset of example interactions based on the campaign prompt
        key_examples = get_vector_store_results(campaign.campaign_prompt, 2, 0.25, {'context': 'sender', 'id': sender.id})

        # get the key_examples["text"] from each example and remove the brackets
        key_examples = [example["text"] for example in key_examples]

        # remove all [ and { }] from the examples
        key_examples = [example.replace("[", "").replace("]", "").replace("{", "").replace("}", "") for example in key_examples]

        prompt_template = '''
            Hey there! You're helping to connect with voters on behalf of {sender_name}. The tone? Let's keep it friendly and straightforward—like chatting with a mature friend. Aim for 1-2 sentences; keep it short and sweet.

            This a template message that will go out to every voter in the campaign. In your message use <VOTER_NAME> to refer to the voter.

            Campaign Details:
            {campaign_prompt}

            What We're Trying to Achieve: 
            {campaign_goal}

            Campaign End Date:
            {campaign_end_date} (Note: that's election day for political races.)

            Sender Information:
            {sender_information}

            Output Format:
            Please provide your responses as plain text only, without any additional formatting, labels, or annotations. The text should be ready to send directly to the voter with just their name to replace <VOTER_NAME>.

            Remember, these are text messages. Do not include any headers or additional context before the first message.
        '''

        system_prompt_template = SystemMessagePromptTemplate.from_template(prompt_template)

        chat_prompt_template = ChatPromptTemplate.from_messages([system_prompt_template])

        self.system_prompt = chat_prompt_template.format(
            sender_name=sender.sender_name,
            campaign_prompt=campaign.campaign_prompt,
            campaign_goal=campaign.campaign_goal,
            campaign_end_date=campaign.campaign_end_date,
            sender_information=sender.sender_information
        )

        super().__init__(self.system_prompt, "campaign_message_agent", "Generates an initial message for a campaign", campaign.id)

        self.conversation_history = initialize_conversation(self.system_prompt)

        db.session.add(self)
        db.session.commit()
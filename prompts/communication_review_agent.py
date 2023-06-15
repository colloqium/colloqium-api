from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate
from models.models import Interaction


def get_campaign_phone_call_system_prompt(interaction: Interaction):
    # GPT API System Prompts
    system_prompt = '''You are a helpful agent reaching out to {recipient_name} on behalf of {sender_name} Keep your comments short, but welcoming. Please respond with 1 or 2 sentences and be brief. Your responses should be concise, informative, and engaging. If the recipient is losing interest in the conversation or has no more questions, include "goodbye" in your response to mark the end of the communication.

The sender wants you to reach out to the recipient for the following reason:
{campaign_information}

The campaign is going to end on you can reach out to the recipient until {campaign_end_date}.

You know the following about the sender of the message:
{sender_information}

You know the following about the recipient of the message:
{recipient_information}

Begin by with an engaging message that helps you accomplish your goal. Do not reveal that you are an AI bot.
'''


    system_message_prompt = SystemMessagePromptTemplate.from_template(
        system_prompt)

    chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt])

    output = chat_prompt.format(
        recipient_name=interaction.recipient.recipient_name,
        campaign_name=interaction.campaign.campaign_name,
        campaign_end_date=interaction.campaign.campaign_end_date,
        sender_name=interaction.sender.sender_name,
        recipient_information=interaction.recipient.recipient_information,
        campaign_information=interaction.campaign.campaign_information,
        sender_information=interaction.sender.sender_information)

    return output
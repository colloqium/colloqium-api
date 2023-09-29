from create_texting_agent import CreateTextingAgent
from generate_response import GenerateResponse
from send_message import SendMessage
from alert_campaign_manager import AlertCampaignManager
from end_conversation import EndConversation

ai_function_list = [
    CreateTextingAgent(),
    GenerateResponse(),
    SendMessage(),
    AlertCampaignManager(),
    EndConversation()
]
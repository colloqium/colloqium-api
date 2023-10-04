from tools.ai_functions.create_texting_agent import CreateTextingAgent
from tools.ai_functions.generate_response import GenerateResponse
from tools.ai_functions.send_message import SendMessage
from tools.ai_functions.alert_campaign_manager import AlertCampaignManager
from tools.ai_functions.end_conversation import EndConversation

ai_function_list = [
    CreateTextingAgent(),
    GenerateResponse(),
    SendMessage(),
    AlertCampaignManager(),
    EndConversation()
]

ai_function_dict = {function.name: function for function in ai_function_list}
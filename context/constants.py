from models.models import InteractionType
from routes.send_text import send_text
from prompts.campaign_volunteer_agent import get_campaign_text_message_system_prompt

INTERACTION_TYPES = {
    "text_message": InteractionType(name="text_message", method=send_text, system_initialization_method=get_campaign_text_message_system_prompt, callback_route="twilio_message_callback"),
}
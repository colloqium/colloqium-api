from models.models import SendingPhoneNumber, InteractionType
from routes.text_message import text_message
from prompts.campaign_volunteer_agent import get_campaign_text_message_system_prompt
from context.apis import twilio_numbers

AVAILABLE_PHONE_NUMBERS = [
    SendingPhoneNumber(country_code=number[:2], phone_number_after_code=number[2:]).get_full_phone_number() for number in twilio_numbers
]

INTERACTION_TYPES = {
    "text_message": InteractionType(name="text_message", method=text_message, system_initialization_method=get_campaign_text_message_system_prompt, callback_route="twilio_message_callback"),
}

STATIC_FOLDER = "../static"
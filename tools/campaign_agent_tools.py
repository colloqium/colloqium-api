import json
from dataclasses import dataclass
from typing import List
from models import VoterCommunication
from logs.logger import logging
import re

class CampaignWorker:
    def __init__(self, name):
        self.name = name

    def make_phone_call(self, goal):
        return "Dummy phone call made by {} with goal: {}".format(self.name, goal)

    def start_a_text_thread(self, goal):
        return "Dummy text thread started by {} with goal: {}".format(self.name, goal)

    def send_email(self, goal):
        return "Dummy email sent by {} with goal: {}".format(self.name, goal)


@dataclass
class OutreachScheduleEntry:
    outreach_date: str
    outreach_type: str
    outreach_goal: str


@dataclass
class VoterProfile:
    interests: List[str]
    preferred_contact_method: str
    engagement_history: List[str]


@dataclass
class CampaignEvent:
    event_date: str
    event_type: str
    event_goal: str
    target_voters: str


class CampaignTools:
    def __init__(self):
        self.outreach_schedule = []
        self.voter_profile = VoterProfile([], "", [])
        self.voter_engagement_history = []
        self.campaign_events = []

    def set_outreach_schedule(self, schedule_json):
        self.outreach_schedule = self.parse_outreach_schedule(schedule_json)
        return "Outreach schedule set"

    def get_outreach_schedule(self):
        return self.serialize_outreach_schedule()

    def update_voter_profile(self, update_to_make):
        self.voter_profile.engagement_history.append(update_to_make)
        return "Voter profile updated: {}".format(update_to_make)

    def get_voter_information(self, question_about_voter):
        return "Dummy response to question about voter: {}".format(question_about_voter)

    def get_voter_engagement_history(self):
        return self.serialize_voter_engagement_history()

    def make_phone_call(self, goal):
        worker = CampaignWorker("Phone Worker")
        return worker.make_phone_call(goal)

    def start_a_text_thread(self, goal):
        worker = CampaignWorker("Text Worker")
        return worker.start_a_text_thread(goal)

    def send_email(self, goal):
        worker = CampaignWorker("Email Worker")
        return worker.send_email(goal)

    def get_recent_news(self, topic):
        return "Dummy response for recent news on topic: {}".format(topic)

    def google_civic_database(self):
        return "Dummy response from Google Civic Database"

    def get_candidate_schedule(self):
        return self.serialize_campaign_events()

    def review_conversation(self, conversation_topic):
        return "Dummy review of conversation on topic: {}".format(conversation_topic)

    @staticmethod
    def parse_outreach_schedule(schedule_json):
        schedule = json.loads(schedule_json)
        return [OutreachScheduleEntry(**entry) for entry in schedule]

    def serialize_outreach_schedule(self):
        return json.dumps([entry.__dict__ for entry in self.outreach_schedule])

    def serialize_voter_engagement_history(self):
        return json.dumps(self.voter_engagement_history)

    def serialize_campaign_events(self):
        return json.dumps([event.__dict__ for event in self.campaign_events])



def extract_action(message):
    action_tag = 'Action:'
    pause_tag = 'PAUSE'

    if action_tag not in message:
        logging.info(f"No action tag found in message: {message}")
        return None, None

    # Extract everything between 'Action:' and 'PAUSE' or end of the string
    start = message.index(action_tag) + len(action_tag)
    end = message.index(pause_tag) if pause_tag in message else None
    action_content = message[start:end].strip()

    # Extract the action name and parameters
    action_match = re.match(r'(\w+)\(([\s\S]*)\)', action_content)
    if action_match:
        action_name = action_match.group(1)

        # Try converting parameters from JSON string to Python object, if fails assume it's a plain string
        action_params_str = action_match.group(2).strip()
        try:
            action_params = json.loads(action_params_str)
        except json.JSONDecodeError:
            action_params = action_params_str  # If not a valid JSON, treat it as a plain string

        return action_name, action_params

    return None, None


def execute_action(campaign_tools: CampaignTools, action_name, action_params):
    logging.info(f"Executing action: {action_name}")
    # Check if the provided action name corresponds to a method in CampaignTools
    if hasattr(campaign_tools, action_name):
        # Retrieve the method from the campaign_tools object
        action_method = getattr(campaign_tools, action_name)
        
        # If the parameters is a list or a dictionary, we will unpack it using **
        # If the parameter is a single value, we will pass it directly
        if isinstance(action_params, list):
            result = action_method(*action_params)
        elif isinstance(action_params, dict):
            result = action_method(**action_params)
        else:
            result = action_method(action_params)

        return result

    # If there is no method with the provided name, return an error message
    return f"There is no available action with name {action_name}"


def update_conversation(voter_communication: VoterCommunication, message):
    """
    This function should append the new message to the voter_communication conversation.
    """
    logging.info(f"Updating conversation with new message: {message}")
    conversation = voter_communication.conversation
    conversation.append({"role": "user", "content": message})
    return
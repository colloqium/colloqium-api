import json
from dataclasses import dataclass
from typing import List
from models import VoterCommunication
from logs.logger import logging
import re
import datetime
from tools.scheduler import scheduler


class CampaignWorker:

    def __init__(self, name):
        self.name = name

    def make_phone_call(self, goal):
        return "Dummy phone call made by {} with goal: {}".format(
            self.name, goal)

    def start_a_text_thread(self, goal):
        return "Dummy text thread started by {} with goal: {}".format(
            self.name, goal)

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

        # Get first outreach from schedule
        first_outreach = filter_outreach(self.outreach_schedule)

        outreach_date = datetime.datetime.strptime(
            first_outreach.outreach_date, '%Y-%m-%d')
        outreach_type = first_outreach.outreach_type
        outreach_goal = first_outreach.outreach_goal

        # Get the function corresponding to the outreach type
        func = outreach_functions.get(outreach_type)

        if func:
            # Schedule the outreach
            scheduler.add_job(func,
                              'date',
                              run_date=outreach_date,
                              args=[outreach_goal])
            scheduler.start()
        else:
            return f"No function defined for outreach type {outreach_type}"

        return "Outreach schedule set"

    def get_outreach_schedule(self):
        return self.serialize_outreach_schedule()

    def update_voter_profile(self, update_to_make):
        self.voter_profile.engagement_history.append(update_to_make)
        return "Voter profile updated: {}".format(update_to_make)

    def get_voter_information(self, question_about_voter):
        return "Dummy response to question about voter: {}".format(
            question_about_voter)

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
        return "Dummy review of conversation on topic: {}".format(
            conversation_topic)

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

    logging.info("Extracting action for agent")
    action_tag = 'Action:'
    pause_tag = 'PAUSE'

    if action_tag not in message:
        logging.info(f"No action tag found in message: {message}")
        return None, None

    # Extract everything between 'Action:' and 'PAUSE' or end of the string
    start = message.index(action_tag) + len(action_tag)
    end = message.index(pause_tag) if pause_tag in message else None
    action_content = message[start:end].strip()

    logging.info(f"Action content: {action_content}")

    # Extract the action name and parameters
    action_match = re.match(r'(\w+)\(([\s\S]*)\)', action_content)
    if action_match:
        logging.info(f"Action match: {action_match}")
        action_name = action_match.group(1)

        logging.info(f"Extracted Action name: {action_name}")

        # Try converting parameters from JSON string to Python object, if fails assume it's a plain string
        action_params_str = action_match.group(2).strip()
        logging.info(f"Action params: {action_params_str}")

        try:
            action_params = json.loads(action_params_str)
        except json.JSONDecodeError:
            action_params = action_params_str  # If not a valid JSON, treat it as a plain string

        return action_name, action_params

    return None, None


def execute_action(campaign_tools: CampaignTools, action_name, action_params):
    logging.info(f"Executing action: {action_name}")
    # Check if the provided action name corresponds to a method in CampaignTools

    result = f"No action named '{action_name}' found in CampaignTools"
    if hasattr(campaign_tools, str(action_name)):

        logging.info("Action exisits in CampaignTools")

        # Retrieve the method from the campaign_tools object
        action_method = getattr(campaign_tools, action_name)

        # Convert action_params into a JSON string if it is a list or dict
        if isinstance(action_params, (list, dict)):
            action_params = json.dumps(action_params)

        # Execute the action method with action_params as an argument
        result = action_method(action_params)
    else:
        logging.info(f"No acution named '{action_name}' found in CampaignTools")
        # If there is no method with the provided name, return an error message
        return f"There is no available action with name {action_name}"
    
    return result

def update_conversation(voter_communication: VoterCommunication, message):
    """
    This function should append the new message to the voter_communication conversation.
    """
    logging.info(f"Updating conversation with new message: {message}")
    conversation = voter_communication.conversation
    conversation.append({"role": "user", "content": message})
    return


def filter_outreach(outreach_list):

    logging.info(f"Filtering list {outreach_list}")

    # Get today's date
    today = datetime.date.today()

    # Convert string dates to datetime objects and compare with today's date
    filtered_list = [
        outreach for outreach in outreach_list if datetime.datetime.strptime(
            outreach.outreach_date, '%Y-%m-%d').date() >= today
    ]

    # If the filtered list is not empty, sort it by date and return the first element
    if filtered_list:
        return sorted(filtered_list,
                      key=lambda k: datetime.datetime.strptime(
                          k.outreach_date, '%Y-%m-%d').date())[0]

    return None


def text_outreach(goal):
    print(f"Sending text: {goal}")


def call_outreach(goal):
    print(f"Making call: {goal}")


def email_outreach(goal):
    print(f"Sending email: {goal}")


# Mapping from outreach type to function
outreach_functions = {
    'text': text_outreach,
    'call': call_outreach,
    'email': email_outreach
}

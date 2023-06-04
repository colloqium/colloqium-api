import json
from models import Interaction, OutreachScheduleEntry
from flask_sqlalchemy import SQLAlchemy
from logs.logger import logging
import re
import datetime
from tools.scheduler import scheduler
from tools.campaign_worker_tools import CampaignWorker, outreach_functions
from tools.utility import remove_trailing_commas


class CampaignTools:

    def __init__(self, communication: Interaction, db: SQLAlchemy):
        self.outreach_schedule = communication.recipient_outreach_schedule
        self.recipient_profile = communication.recipient.recipient_profile
        self.db = db
        self.recipient_engagement_history = communication.recipient.recipient_engagement_history
        self.campaign_events = communication.candidate.candidate_schedule
        self.communication = communication

    def set_outreach_schedule(self, schedule_json, communication_id):

        #confirm we are working on the communication you expect.
        if communication_id != self.communication.id:
            logging.error(
                "We are not working on the communication you expect.")
            return f"You are not working on the communication you expect. Expected: {self.communication.id} Actual: {communication_id}"

        logging.info("Setting outreach schedule for campaign agent.")

        self.outreach_schedule = self.parse_outreach_schedule(schedule_json)

        logging.info(f"Outreach schedule set to: {self.outreach_schedule}")

        # Get first outreach from schedule
        next_outreach = filter_outreach(self.outreach_schedule)
        logging.info(f"Next outreach is: {next_outreach}")

        # outreach_date = datetime.datetime.strptime(next_outreach.outreach_date, '%Y-%m-%d %H:%M:%S')

        outreach_type = next_outreach.outreach_type
        outreach_goal = next_outreach.outreach_goal
        outreach_date = datetime.datetime.now() + datetime.timedelta(
            seconds=20)  # outreach_date will be 20 seconds from now

        # Get the function corresponding to the outreach type
        func = outreach_functions.get(outreach_type)

        if func:
            # Schedule the outreach
            scheduler.add_job(func,
                              'date',
                              run_date=outreach_date,
                              args=[self.communication.id, outreach_goal])
            scheduler.start()
            logging.info(
                f"Outreach scheduled for {outreach_type} with goal: {outreach_goal}"
            )
        else:
            logging.error(f"Outreach type not supported: {outreach_type}")
            return f"No function defined for outreach type {outreach_type}"

        self.db.session.commit()
        return f"Outreach schedule set for {outreach_date} with outreach goal {outreach_goal}"

    def get_outreach_schedule(self, communication_id):
        return self.serialize_outreach_schedule()

    def update_recipient_profile(self, update_to_make, communication_id):
        self.recipient_profile.engagement_history.append(update_to_make)
        return "recipient profile updated: {}".format(update_to_make)

    def get_recipient_information(self, question_about_recipient, communication_id):
        return "Dummy response to question about recipient: {}".format(
            question_about_recipient)

    def get_recipient_engagement_history(self, communication_id):
        return self.serialize_recipient_engagement_history()

    def make_phone_call(self, goal, communication_id):
        worker = CampaignWorker("Phone Worker")
        return worker.make_phone_call(goal)

    def start_a_text_thread(self, goal, communication_id):
        worker = CampaignWorker(self.communication)
        return worker.start_a_text_thread(goal)

    def send_email(self, goal, communication_id):
        worker = CampaignWorker("Email Worker")
        return worker.send_email(goal)

    def get_recent_news(self, topic, communication_id):
        return "Dummy response for recent news on topic: {}".format(topic)

    def google_civic_database(self, question, communication_id):
        return "Dummy response from Google Civic Database"

    def get_candidate_schedule(self, communication_id):
        return self.serialize_campaign_events()

    def review_conversation(self, conversation_topic):
        return "Dummy review of conversation on topic: {}".format(
            conversation_topic)

    @staticmethod
    def parse_outreach_schedule(schedule_json):
        logging.info(f"Parsing schedule json: {schedule_json}")
        json_remove_trailing_number = re.split('(?<=\]),', schedule_json)[0]
        json_remove_trailing_comma = remove_trailing_commas(json_remove_trailing_number)
        schedule = json.loads(json_remove_trailing_comma)
        return [OutreachScheduleEntry(**entry) for entry in schedule]

    def serialize_outreach_schedule(self):
        return json.dumps([entry.__dict__ for entry in self.outreach_schedule])

    def serialize_recipient_engagement_history(self):
        return json.dumps(self.recipient_engagement_history)

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
        result = action_method(action_params, campaign_tools.communication.id)
    else:
        logging.info(
            f"No acition named '{action_name}' found in CampaignTools")
        # If there is no method with the provided name, return an error message
        return f"There is no available action with name {action_name}"

    return result


def filter_outreach(outreach_list):

    logging.info(f"Filtering list {outreach_list}")

    # Get today's date
    today = datetime.date.today()

    # Convert string dates to datetime objects and compare with today's date
    filtered_list = [
        outreach for outreach in outreach_list if datetime.datetime.strptime(
            outreach.outreach_date, '%Y-%m-%d %H:%M:%S').date() >= today
    ]

    # If the filtered list is not empty, sort it by date and return the first element
    if filtered_list:
        return sorted(filtered_list,
                      key=lambda k: datetime.datetime.strptime(
                          k.outreach_date, '%Y-%m-%d %H:%M:%S').date())[0]

    return None

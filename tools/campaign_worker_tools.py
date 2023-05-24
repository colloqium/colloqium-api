from models import VoterCommunication
from logs.logger import logging
from database import db
from context import app
from prompts.campaign_volunteer_agent import get_campaign_phone_call_system_prompt, get_campaign_text_message_system_prompt
from tools.utility import initialize_conversation, add_llm_response_to_conversation, add_message_to_conversation
import requests
import os


class CampaignWorker:

    def __init__(self, communication: VoterCommunication):
        self.communication = communication

    def make_phone_call(self, goal):
        voter = self.communication.voter
        logging.info(f"Starting a phone call with voter: {voter.voter_name}")
        return f"Dummy Phone Call with Goal: {goal}"

    def start_a_text_thread(self, goal):
        voter = self.communication.voter
        new_texting_thread = initialize_voter_outreach_thread(
            self.communication, goal, "text")
        logging.info(f"Starting a text thread with voter: {voter.voter_name}")

        first_message = add_llm_response_to_conversation(new_texting_thread)

        updated_conversation = add_message_to_conversation(new_texting_thread, first_message)

        new_texting_thread.conversation = updated_conversation

        logging.info(f"First message: {new_texting_thread.conversation}")
        db.session.add(new_texting_thread)
        db.session.commit()

        logging.info(f"Texting thread id after db commit {new_texting_thread.id}")

        new_texting_thread = db.session.query(VoterCommunication).filter(
            VoterCommunication.id == new_texting_thread.id).first()     
        # Include voter_communication_id in the URL

        logging.info(f"Texting with id: {new_texting_thread.id}")
        logging.info(f"Texting with conversation: {new_texting_thread.conversation}")
        url = os.environ['BASE_URL'] + f"text_message/{new_texting_thread.id}"

        response = requests.post(url)
        return f"Attempted text and got re: {response.text}"

    def send_email(self, goal):
        voter = self.communication.voter
        logging.info(f"Starting an email with voter: {voter.voter_name}")
        return f"Dummy email sent with goal: {goal}"


def text_outreach(communication_id, goal):
    logging.info(
        f"Scheduling a text outreach with communicaiton id: {communication_id} and goal: {goal}"
    )
    with app.app_context():
        communication = db.session.query(VoterCommunication).get(
            communication_id)  # get the instance fresh from the DB
        logging.info(f"Got the communication instance: {communication}")
        worker = CampaignWorker(
            communication
        )  # create a new CampaignWorker with the fresh communication instance
        worker.start_a_text_thread(goal)

    print(f"Sending text: {goal}")


def call_outreach(communication_id, goal):
    with app.app_context():
        communication = db.session.query(VoterCommunication).get(
            communication_id)  # get the instance fresh from the DB

        worker = CampaignWorker(
            communication
        )  # create a new CampaignWorker with the fresh communication instance
        worker.make_phone_call(goal)
    print(f"Making Call: {goal}")


def email_outreach(communication_id, goal):
    with app.app_context():
        communication = db.session.query(VoterCommunication).get(
            communication_id)  # get the instance fresh from the DB

        worker = CampaignWorker(
            communication
        )  # create a new CampaignWorker with the fresh communication instance
        worker.send_email(goal)

    print(f"Sending email: {goal}")


# Mapping from outreach type to function
outreach_functions = {
    'text': text_outreach,
    'call': call_outreach,
    'email': email_outreach
}


def initialize_voter_outreach_thread(
        voter_communication: VoterCommunication, goal: str,
        communication_type: str) -> VoterCommunication:
    if communication_type == "call":
        # Add information from VoterCallForm to the system prompt
        system_prompt = get_campaign_phone_call_system_prompt(
            voter_communication)
    elif communication_type == "text":
        system_prompt = get_campaign_text_message_system_prompt(
            voter_communication)
    else:
        logging.error(f"Invalid communication type: {communication_type}")
        raise Exception(f"Invalid communication type: {communication_type}")

    #Pre create the first response
    conversation = initialize_conversation(system_prompt)

    # Create the VoterCommunication
    outreach_communication_thread = VoterCommunication(
        twilio_conversation_sid='',  # You will need to update this later
        conversation=conversation,
        voter=voter_communication.voter,  # The ID of the voter
        candidate=voter_communication.candidate,
        race=voter_communication.race,
        communication_type=communication_type)

    db.session.add(outreach_communication_thread)
    db.session.commit()

    #retrieve filled out VoterCommunication from database
    outreach_communication_thread = db.session.query(VoterCommunication).get(
        outreach_communication_thread.id)
    logging.info(
        f"Created outreach communication thread: {outreach_communication_thread}"
    )

    return outreach_communication_thread

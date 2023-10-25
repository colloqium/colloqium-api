from models.interaction import Interaction
from logs.logger import logging
from context.database import db
from flask import current_app
from prompts.campaign_volunteer_agent import get_campaign_phone_call_system_prompt, get_campaign_text_message_system_prompt
from tools.utility import initialize_conversation, get_llm_response_to_conversation, add_message_to_conversation
import requests
import os


class CampaignWorker:

    def __init__(self, communication: Interaction):
        self.communication = communication

    def make_phone_call(self, goal):
        votert = self.communication.voter
        print(f"Starting a phone call with votert: {votert.votert_name}")
        return f"Dummy Phone Call with Goal: {goal}"

    def start_a_text_thread(self, goal):
        votert = self.communication.votert
        new_texting_thread = initialize_votert_outreach_thread(
            self.communication, goal, "text")
        print(f"Starting a text thread with votert: {votert.votert_name}")

        first_message = get_llm_response_to_conversation(new_texting_thread.conversation)

        updated_conversation = add_message_to_conversation(new_texting_thread.conversation, first_message)

        new_texting_thread.conversation = updated_conversation

        print(f"First message: {new_texting_thread.conversation}")
        db.session.add(new_texting_thread)
        db.session.commit()
        ()

        print(f"Texting thread id after db commit {new_texting_thread.id}")

        new_texting_thread = db.session.query(Interaction).filter(
            Interaction.id == new_texting_thread.id).first()     
        # Include votert_communication_id in the URL

        print(f"Texting with id: {new_texting_thread.id}")
        print(f"Texting with conversation: {new_texting_thread.conversation}")
        url = os.environ['BASE_URL'] + f"text_message/{new_texting_thread.id}"

        response = requests.post(url)
        return f"Attempted text and got re: {response.text}"

    def send_email(self, goal):
        votert = self.communication.votert
        print(f"Starting an email with votert: {votert.votert_name}")
        return f"Dummy email sent with goal: {goal}"


def text_outreach(communication_id, goal):
    print(
        f"Scheduling a text outreach with communicaiton id: {communication_id} and goal: {goal}"
    )
    with current_app.app_context():
        communication = db.session.query(Interaction).get(
            communication_id)  # get the instance fresh from the DB
        print(f"Got the communication instance: {communication}")
        worker = CampaignWorker(
            communication
        )  # create a new CampaignWorker with the fresh communication instance
        worker.start_a_text_thread(goal)

    print(f"Sending text: {goal}")


def call_outreach(communication_id, goal):
    with current_app.app_context():
        communication = db.session.query(Interaction).get(
            communication_id)  # get the instance fresh from the DB

        worker = CampaignWorker(
            communication
        )  # create a new CampaignWorker with the fresh communication instance
        worker.make_phone_call(goal)
    print(f"Making Call: {goal}")


def email_outreach(communication_id, goal):
    with current_app.app_context():
        communication = db.session.query(Interaction).get(
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


def initialize_votert_outreach_thread(
        votert_communication: Interaction, goal: str,
        communication_type: str) -> Interaction:
    if communication_type == "call":
        # Add information from votertCallForm to the system prompt
        system_prompt = get_campaign_phone_call_system_prompt(
            votert_communication)
    elif communication_type == "text":
        system_prompt = get_campaign_text_message_system_prompt(
            votert_communication)
    else:
        logging.error(f"Invalid communication type: {communication_type}")
        raise Exception(f"Invalid communication type: {communication_type}")

    #Pre create the first response
    conversation = initialize_conversation(system_prompt)

    # Create the votertCommunication
    outreach_communication_thread = Interaction(
        twilio_conversation_sid='',  # You will need to update this later
        conversation=conversation,
        votert=votert_communication.votert,  # The ID of the votert
        candidate=votert_communication.candidate,
        race=votert_communication.race,
        communication_type=communication_type)

    db.session.add(outreach_communication_thread)
    db.session.commit()
    ()

    #retrieve filled out votertCommunication from database
    outreach_communication_thread = db.session.query(Interaction).get(
        outreach_communication_thread.id)
    print(
        f"Created outreach communication thread: {outreach_communication_thread}"
    )

    return outreach_communication_thread

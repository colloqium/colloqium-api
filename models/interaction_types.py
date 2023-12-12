from routes.send_text import send_text
from routes.make_robo_call import make_robo_call
from dataclasses import dataclass
from datetime import datetime as DateTime
from models.voter import Voter
from models.sender import Sender

#enum with the different types of interactions. Call, Text, Email, and Plan
@dataclass
class InteractionType:
    name: str
    method: callable
    system_initialization_method: callable
    callback_route: str

    # should define two methods for all children initialize, update, send
    

    def __init__(self, name: str, method: callable, callback_route: str):
        self.name = name
        self.method = method
        self.callback_route = callback_route

    def __str__(self):
        return self.name


class EventType:
    VOLUNTEER = "volunteer"
    FUNDRAISER = "fundraiser"
    VOTER_OUTREACH = "voter_outreach"
    ELECTION = "election"

@dataclass
class Event:
    event_name: str
    event_description: str
    event_date: DateTime
    event_type: EventType
    event_goal: str
    event_outcome: str
    target_attendee : str

@dataclass
class Donation:
    donation_date: DateTime
    donation_amount: float
    donor: Voter
    donation_recipient: Sender

@dataclass
class VoterFunnelStage:
    UNCONTACTED = 1
    IDED = 2
    PERSUADAABLE = 3
    ACTIVATABLE = 4
    REGISTERED = 5
    VOTING_PLAN = 6
    VOTED = 7

@dataclass
class OutreachScheduleEntry:
    outreach_date: DateTime
    outreach_type: str
    outreach_goal: str

INTERACTION_TYPES = {
    "text_message": InteractionType(name="text_message", method=send_text, callback_route="interaction_callback"),
    "robo_call": InteractionType(name="robo_call", method=make_robo_call, callback_route="interaction_callback"),
}
from sqlalchemy import DateTime
from context.database import db
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from typing import List
from dataclasses import dataclass
from wtforms.validators import Regexp


@dataclass
class OutreachScheduleEntry:
    outreach_date: str
    outreach_type: str
    outreach_goal: str


@dataclass
class RecipientProfile:
    interests: List[str]
    preferred_contact_method: str
    engagement_history: List[str]


@dataclass
class Event:
    event_date: str
    event_type: str
    event_goal: str
    target_attendee : str


#enum with the different types of interactions. Call, Text, Email, and Plan
@dataclass
class InteractionType:
    name: str
    method: callable
    system_initialization_method: callable
    callback_route: str

    #String representation that removes underscores and capitalizes the first letter of each word
    def __str__(self):
        return self.name.replace("_", " ").capitalize()

@dataclass
class InteractionStatus:
    INITIALIZED = "initialized"
    HUMAN_CONFIRMED = "human_confirmed"
    SENT = "sent"

@dataclass
class SendingPhoneNumber:
    country_code: str
    phone_number_after_code: str

    def __post_init__(self):
        self.country_code_validator = Regexp(
            # The regular expression to match country codes
            r'^\+\d$',
            # The error message to display if the country code is invalid
            message=
            'The country code must be in the format +1# where # is a digit'
        )

    # Create a string that is the country code and phone number in the format +1##########
    def get_full_phone_number(self):
        return self.country_code + self.phone_number_after_code

    def validate(self):
        return self.country_code_validator(self.country_code)


class Recipient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    recipient_name = db.Column(db.String(50))
    recipient_information = db.Column(db.Text)
    recipient_phone_number = db.Column(db.String(100))
    recipient_profile = db.Column(db.JSON())
    recipient_engagement_history = db.Column(db.JSON())
    # Add relationship
    interactions = relationship('Interaction',
                                  backref='recipient',
                                  lazy=True)


class Sender(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_name = db.Column(db.String(50))
    sender_information = db.Column(db.Text)
    sender_schedule = db.Column(db.JSON())
    sender_phone_number = db.Column(db.String(100))
    # Add relationship
    interactions = relationship('Interaction',
                                  backref='sender',
                                  lazy=True)


class Campaign(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    campaign_name = db.Column(db.String(50))
    campaign_information = db.Column(db.Text)
    campaign_end_date = db.Column(db.Date)

    # Add relationship
    interactions = relationship('Interaction',
                                  backref='campaign',
                                  lazy=True)


class Interaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    twilio_conversation_sid = db.Column(db.String(50))
    conversation = db.Column(db.JSON())
    interaction_type = db.Column(db.String(50))
    interaction_goal = db.Column(db.Text)
    recipient_id = db.Column(db.Integer, db.ForeignKey('recipient.id'))
    sender_id = db.Column(db.Integer, db.ForeignKey('sender.id'))
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'))
    recipient_outreach_schedule = db.Column(db.JSON())
    interaction_status = db.Column(db.String(50)) #initialized, human_confirmed, sent
    time_created = db.Column(DateTime(timezone=True), server_default=func.now())
    time_updated = db.Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships are set up in Recipient, Sender, and CampaignContext models
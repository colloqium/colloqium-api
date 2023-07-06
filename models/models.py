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


class BaseModel(db.Model):
    __abstract__ = True

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class Recipient(BaseModel):
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


class Interaction(BaseModel):
    id = db.Column(db.Integer, primary_key=True)
    twilio_conversation_sid = db.Column(db.String(50))
    conversation = db.Column(db.JSON())
    interaction_type = db.Column(db.String(50))
    interaction_goal = db.Column(db.Text)
    recipient_id = db.Column(db.Integer, db.ForeignKey('recipient.id'))
    sender_id = db.Column(db.Integer, db.ForeignKey('sender.id'), name="sender_id")
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'))
    recipient_outreach_schedule = db.Column(db.JSON())
    interaction_status = db.Column(db.String(50)) #initialized, human_confirmed, sent
    time_created = db.Column(DateTime(timezone=True), server_default=func.now())
    time_updated = db.Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships are set up in Recipient, Sender, and CampaignContext models

    #overwrite to_dict method to include the sender and recipient and the conversation object
    def to_dict(self):
        interaction_dict = super().to_dict()
        interaction_dict["sender"] = self.sender.to_dict()
        interaction_dict["recipient"] = self.recipient.to_dict()
        
        # Assign conversation list directly
        interaction_dict["conversation"] = self.conversation if self.conversation else []

        return interaction_dict


class Sender(BaseModel):
    id = db.Column(db.Integer, primary_key=True)
    sender_name = db.Column(db.String(50))
    sender_information = db.Column(db.Text)
    sender_schedule = db.Column(db.JSON())
    # Add relationship
    interactions = relationship('Interaction',
                                  backref='sender',
                                  lazy=True)
    phone_numbers = relationship('PhoneNumber',
                                  backref='sender',
                                  lazy=True)
    
    def select_phone_number_for_interaction(self, interaction: Interaction):
        print(f"Selecting phone number for interaction {interaction.id}")
        return self.phone_numbers[0].get_full_phone_number()
    
    #overwrite the base to_dict method to include the phone numbers
    def to_dict(self):
        sender_dict = super().to_dict()
        sender_dict["phone_numbers"] = [phone_number.get_full_phone_number() for phone_number in self.phone_numbers]
        return sender_dict


class Campaign(BaseModel):
    id = db.Column(db.Integer, primary_key=True)
    campaign_name = db.Column(db.String(50))
    campaign_information = db.Column(db.Text)
    sender_id = db.Column(db.Integer, db.ForeignKey('sender.id'), name="sender_id")
    campaign_end_date = db.Column(db.Date)

    # Add relationship
    interactions = relationship('Interaction',
                                  backref='campaign',
                                  lazy=True)
    
    # modify the to_dict method to include the sender
    def to_dict(self):
        campaign_dict = super().to_dict()
        # get the sender from the sender_id
        sender = Sender.query.get(self.sender_id)
        campaign_dict["sender"] = sender.to_dict()
        return campaign_dict

class PhoneNumber(BaseModel):
    id = db.Column(db.Integer, primary_key=True)
    country_code = db.Column(db.String(10))
    phone_number_after_code = db.Column(db.String(20))
    sender_id = db.Column(db.Integer, db.ForeignKey('sender.id'), name="sender_id")

    def __init__(self, full_phone_number):
        # Find the index of the last 10 digits of the phone number
        last_10_digits_index = len(full_phone_number) - 10

        # Extract the last 10 digits of the phone number
        self.phone_number_after_code = full_phone_number[last_10_digits_index:]

        # Extract the country code from the beginning of the phone number
        self.country_code = full_phone_number[:last_10_digits_index]

    def get_full_phone_number(self):
        return f"{self.country_code}{self.phone_number_after_code}"
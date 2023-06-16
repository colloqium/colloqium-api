from context.database import db
from sqlalchemy.orm import relationship
from typing import List
from dataclasses import dataclass


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
    CALL = "call"
    TEXT = "text"
    EMAIL = "email"
    PLAN = "plan"
    EVENT = "event"

    @classmethod
    def choices(cls):
        return [(getattr(cls, name), name.capitalize()) for name in dir(cls) if not name.startswith("_") and isinstance(getattr(cls, name), str)]

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

    # Relationships are set up in Recipient, Sender, and CampaignContext models
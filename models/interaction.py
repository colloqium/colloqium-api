from sqlalchemy import DateTime
from context.database import db
from models.sender import Sender
from models.voter import Voter
from models.base_db_model import BaseDbModel
from sqlalchemy.sql import func
from enum import Enum as PyEnum
from dataclasses import dataclass


@dataclass
class InteractionStatus:
    CREATED = 1
    INITIALIZED = 2
    HUMAN_CONFIRMED = 3
    SENT = 4
    DELIVERED = 5
    RESPONDED = 6
    CONVERTED = 7
    OPTED_OUT = 8

class Interaction(BaseDbModel):
    id = db.Column(db.Integer, primary_key=True)
    twilio_conversation_sid = db.Column(db.String(50))
    conversation = db.Column(db.JSON())
    interaction_type = db.Column(db.String(50))
    interaction_goal = db.Column(db.Text)
    voter_id = db.Column(db.Integer, db.ForeignKey('voter.id'))
    sender_id = db.Column(db.Integer, db.ForeignKey('sender.id'), name="sender_id")
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'))
    agent_id = db.Column(db.Integer, db.ForeignKey('agent.id'))
    voter_outreach_schedule = db.Column(db.JSON())
    interaction_status = db.Column(db.Integer) #initialized, human_confirmed, sent, delivered, responded, converted
    time_created = db.Column(DateTime(timezone=True), server_default=func.now())
    time_updated = db.Column(DateTime(timezone=True), onupdate=func.now())

    # Evaluation of the interaction
    goal_achieved = db.Column(db.Boolean())
    rating_explanation = db.Column(db.Text())
    rating = db.Column(db.Integer())
    campaign_relevance_score = db.Column(db.Integer()) # how interesting this interaction would be for the sender to know about
    campaign_relevance_explanation = db.Column(db.Text())
    campaign_relevance_summary = db.Column(db.Text())

    #Summary of interaction to aggregate useful takeaways
    insights_about_issues = db.Column(db.JSON())
    insights_about_voter = db.Column(db.Text())

    # Relationships are set up in Recipient, Sender, and CampaignContext models
    
    def select_phone_number(self):
        sender = Sender.query.get(self.sender_id)
        return sender.phone_numbers[0].get_full_phone_number()

    def select_email(self):
        sender = Sender.query.get(self.sender_id)
        return sender.sender_email

    #overwrite to_dict method to include the sender and recipient and the conversation object
    def to_dict(self):
        interaction_dict = super().to_dict()
        #lookup the sender from the id
        sender = Sender.query.get(self.sender_id)
        interaction_dict["sender"] = sender.to_dict()

        #lookup the recipient from the id
        voter = Voter.query.get(self.voter_id)
        interaction_dict["voter"] = voter.to_dict()
        
        # Assign conversation list directly
        interaction_dict["conversation"] = self.conversation if self.conversation else []

        interaction_dict['insights_about_issues'] = self.insights_about_issues

        return interaction_dict


@dataclass
class SenderVoterRelationship(BaseDbModel):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('sender.id'))
    voter_id = db.Column(db.Integer, db.ForeignKey('voter.id'))
    funnel_stage = db.Column(db.String(50))
    opted_out = db.Column(db.Boolean())
    
    # New SQLAlchemy relationship
    agents = db.relationship('Agent', backref='sender_voter_relationship')



class AlertStatus(PyEnum):
    SENT = 1
    SEEN = 2
    PROCESSED = 3

    to_dict = lambda self: self.name.lower()


@dataclass
class Alert(BaseDbModel):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('sender.id'))
    voter_id = db.Column(db.Integer, db.ForeignKey('voter.id'))
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'))
    alert_time = db.Column(DateTime(timezone=True), server_default=func.now())
    alert_message = db.Column(db.Text())
    alert_status = db.Column(db.Enum(AlertStatus), default=AlertStatus.SENT)

    def to_dict(self):
        alert_dict = super().to_dict()
        sender = Sender.query.get(self.sender_id)
        alert_dict["sender"] = sender.to_dict()
        voter = Voter.query.get(self.voter_id)
        alert_dict["voter"] = voter.to_dict()
        alert_dict["alert_status"] = self.alert_status.name.lower()
        return alert_dict
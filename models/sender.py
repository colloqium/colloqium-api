from sqlalchemy import DateTime
from context.database import db
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from typing import List
from dataclasses import dataclass
from wtforms.validators import Regexp
from models.base_db_model import BaseDbModel
from models.association_tables import audience_voter, campaign_audience

class Sender(BaseDbModel):
    id = db.Column(db.Integer, primary_key=True)
    sender_name = db.Column(db.String(50))
    sender_information = db.Column(db.Text)
    sender_schedule = db.Column(db.JSON())
    # Add relationship
    interactions = relationship('Interaction',
                                  backref='sender',
                                  lazy=True)
    voter_relationships = relationship('SenderVoterRelationship',backref='sender',lazy=True)
    phone_numbers = relationship('PhoneNumber',
                                  backref='sender',
                                  lazy=True)
    
    #overwrite the base to_dict method to include the phone numbers
    def to_dict(self):
        sender_dict = super().to_dict()
        sender_dict["phone_numbers"] = [phone_number.get_full_phone_number() for phone_number in self.phone_numbers]
        return sender_dict


#Audience which is a group of voters. voters can be in multiple audiences

class Audience(BaseDbModel):
    id = db.Column(db.Integer, primary_key=True)
    audience_name = db.Column(db.String(50))
    audience_information = db.Column(db.Text)
    sender_id = db.Column(db.Integer, db.ForeignKey('sender.id'), name="sender_id")
    voters = relationship('Voter', secondary=audience_voter, back_populates='audiences')
    campaigns = relationship('Campaign', secondary=campaign_audience, back_populates='audiences')

    # modify the to_dict method to include the sender and the ids of the voters
    def to_dict(self):
        audience_dict = super().to_dict()
        # get the sender from the sender_id
        sender = Sender.query.get(self.sender_id)
        audience_dict["sender"] = sender.to_dict()
        # get the voters object from the voter ids
        audience_dict["voters"] = [voter.to_dict() for voter in self.voters]
        return audience_dict


class Campaign(BaseDbModel):
    id = db.Column(db.Integer, primary_key=True)
    campaign_name = db.Column(db.String(50))
    campaign_prompt = db.Column(db.Text)
    campaign_goal = db.Column(db.Text)
    campaign_fallback = db.Column(db.Text)
    example_interactions = db.Column(db.Text) # "Message bible" of example texts for the campaign
    sender_id = db.Column(db.Integer, db.ForeignKey('sender.id'), name="sender_id")
    campaign_end_date = db.Column(db.Date)

    #Fields for sharing insights on campaign
    campaign_manager_summary = db.Column(db.Text)
    communications_director_summary = db.Column(db.Text)
    field_director_summary = db.Column(db.Text)

    #Fields for measuring outcomes of campaign
    interactions_sent = db.Column(db.Integer)
    interactions_delivered = db.Column(db.Integer)
    interactions_responded = db.Column(db.Integer)
    interactions_converted = db.Column(db.Integer)

    # Add relationship
    interactions = relationship('Interaction',
                                  backref='campaign',
                                  lazy=True)

    audiences = relationship('Audience', secondary=campaign_audience, back_populates='campaigns')
    
    # modify the to_dict method to include the sender
    def to_dict(self):
        campaign_dict = super().to_dict()
        # get the sender from the sender_id
        sender = Sender.query.get(self.sender_id)
        campaign_dict["sender"] = sender.to_dict()

        #audiences can belong to multiple campaigns
        campaign_dict["audiences"] = [audience.to_dict() for audience in self.audiences]
        return campaign_dict

class PhoneNumber(BaseDbModel):
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
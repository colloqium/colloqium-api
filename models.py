from database import db
from sqlalchemy.orm import relationship
from typing import List
from dataclasses import dataclass


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


class Voter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    voter_name = db.Column(db.String(50))
    voter_information = db.Column(db.Text)
    voter_phone_number = db.Column(db.String(100))
    voter_profile = db.Column(db.JSON())
    voter_engagement_history = db.Column(db.JSON())
    # Add relationship
    communications = relationship('VoterCommunication',
                                  backref='voter',
                                  lazy=True)


class Candidate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    candidate_name = db.Column(db.String(50))
    candidate_information = db.Column(db.Text)
    candidate_schedule = db.Column(db.JSON())
    # Add relationship
    communications = relationship('VoterCommunication',
                                  backref='candidate',
                                  lazy=True)


class Race(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    race_name = db.Column(db.String(50))
    race_information = db.Column(db.Text)
    race_date = db.Column(db.Date)

    # Add relationship
    communications = relationship('VoterCommunication',
                                  backref='race',
                                  lazy=True)


class VoterCommunication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    twilio_conversation_sid = db.Column(db.String(50))
    conversation = db.Column(db.JSON())
    communication_type = db.Column(db.String(50))
    communication_goal = db.Column(db.Text)
    voter_id = db.Column(db.Integer, db.ForeignKey('voter.id'))
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidate.id'))
    race_id = db.Column(db.Integer, db.ForeignKey('race.id'))
    voter_outreach_schedule = db.Column(db.JSON())

    # Relationships are set up in Voter, Candidate, and Race models

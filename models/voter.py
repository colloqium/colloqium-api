from context.database import db
from models.base_db_model import BaseDbModel
from models.association_tables import audience_voter
from models.sender import Audience
from sqlalchemy.orm import relationship

class Voter(BaseDbModel):
    id = db.Column(db.Integer, primary_key=True)
    voter_name = db.Column(db.String(50))
    voter_phone_number = db.Column(db.String(100))
    voter_email = db.Column(db.String(100))
    voter_profile = relationship('VoterProfile', backref='voter', lazy='joined', uselist=False)
    interactions = relationship('Interaction', backref='voter', lazy='dynamic')
    audiences = relationship('Audience', secondary=audience_voter, back_populates='voters')
    sender_relationships = relationship('SenderVoterRelationship', backref='voter', lazy='dynamic')

    def to_dict(self):
        voter_dict = super().to_dict()
        voter_dict["sender_relationships"] = [relationship.to_dict() for relationship in self.sender_relationships]
        voter_dict["voter_profile"] = self.voter_profile.to_dict() if self.voter_profile else None
        return voter_dict


class VoterProfile(BaseDbModel):
    id = db.Column(db.Integer, primary_key=True)
    voter_id = db.Column(db.Integer, db.ForeignKey('voter.id'), unique=True)
    interests = db.Column(db.Text)
    policy_preferences = db.Column(db.Text)
    background = db.Column(db.Text)
    last_interaction = db.Column(db.Text)
    preferred_contact_method = db.Column(db.Text)
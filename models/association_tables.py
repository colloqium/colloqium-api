from sqlalchemy import DateTime
from context.database import db
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from typing import List
from dataclasses import dataclass
from wtforms.validators import Regexp

# association table
audience_voter = db.Table('audience_voter',
    db.Column('audience_id', db.Integer, db.ForeignKey('audience.id')),
    db.Column('voter_id', db.Integer, db.ForeignKey('voter.id'))
)

campaign_audience = db.Table('campaign_audience',
    db.Column('campaign_id', db.Integer, db.ForeignKey('campaign.id'), primary_key=True),
    db.Column('audience_id', db.Integer, db.ForeignKey('audience.id'), primary_key=True)
)
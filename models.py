from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)

# Set the SQLALCHEMY_DATABASE_URI configuration variable
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'

# Create a db object using the SQLAlchemy class
db = SQLAlchemy(app)

# Settings for migrations
migrate = Migrate(app, db)


class Voter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    voter_name = db.Column(db.String(50))
    voter_information = db.Column(db.Text)
    voter_phone_number = db.Column(db.String(100))


class Candidate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    candidate_name = db.Column(db.String(50))
    candidate_information = db.Column(db.Text)


class Race(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    race_name = db.Column(db.String(50))
    race_information = db.Column(db.Text)
    race_date = db.Column(db.Date)


class VoterCommunication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    twilio_conversation_sid = db.Column(db.String(50))
    conversation = db.Column(db.JSON())
    communication_type = db.Column(db.String(50))
    voter_id = db.Column(db.Integer, db.ForeignKey('voter.id'))
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidate.id'))
    race_id = db.Column(db.Integer, db.ForeignKey('race.id'))


with app.app_context():
    db.create_all()

import pytest
from flask import url_for
from flask_testing import TestCase
from main import app, db
from model import Voter, Candidate, Race, VoterCommunication
from twilio.twiml.voice_response import VoiceResponse
from twilio.twiml.messaging_response import MessagingResponse


class MyTest(TestCase):

    def create_app(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['CALL_WEBHOOK_URL'] = 'http://mockurlfortesting.com'
        return app

    def setUp(self):
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_home_route(self):
        response = self.client.get('/')
        self.assertRedirects(
            response,
            url_for('voter_communication',
                    last_action="LoadingServerForTheFirstTime"))

    def test_voter_communication_route_get(self):
        response = self.client.get(
            url_for('voter_communication', last_action="TestAction"))
        self.assert200(response)
        self.assert_template_used('voter_communication.html')

    def test_voter_communication_route_post(self):
        response = self.client.post(url_for('voter_communication',
                                            last_action="TestAction"),
                                    data={
                                        'voter_name': 'John Doe',
                                        'voter_phone_number': '+1234567890',
                                        'voter_information': 'Test voter',
                                        'candidate_name': 'Jane Smith',
                                        'candidate_information':
                                        'Test candidate',
                                        'race_name': 'Test Race',
                                        'race_information': 'Test race',
                                        'communication_type': 'call'
                                    })
        self.assertRedirects(response, url_for('call'))
        voter = Voter.query.filter_by(voter_name='John Doe').first()
        self.assertIsNotNone(voter)
        candidate = Candidate.query.filter_by(
            candidate_name='Jane Smith').first()
        self.assertIsNotNone(candidate)
        race = Race.query.filter_by(race_name='Test Race').first()
        self.assertIsNotNone(race)

    def test_twilio_call_route(self):
        # Create a test VoterCommunication
        voter_communication = VoterCommunication(
            twilio_conversation_sid='TestSid',
            conversation=[{
                "role": "system",
                "content": "Test system message"
            }],
            communication_type='call',
            voter_id=1)
        db.session.add(voter_communication)
        db.session.commit()

        response = self.client.post(url_for('twilio_call'),
                                    data={
                                        'CallSid': 'TestSid',
                                        'SpeechResult': 'Test speech result'
                                    })
        self.assert200(response)
        self.assertEqual(response.mimetype, 'text/xml')
        self.assertTrue(isinstance(response.response, VoiceResponse))

    def test_twilio_message_route(self):
        # Create a test VoterCommunication
        voter_communication = VoterCommunication(
            twilio_conversation_sid='TestSid',
            conversation=[{
                "role": "system",
                "content": "Test system message"
            }],
            communication_type='text',
            voter_id=1)
        db.session.add(voter_communication)
        db.session.commit()

        response = self.client.post(url_for('twilio_message'),
                                    data={
                                        'From': '+1234567890',
                                        'Body': 'Test message body'
                                    })
        self.assert200(response)
        self.assertEqual(response.mimetype, 'text/xml')
        self.assertTrue(isinstance(response.response, MessagingResponse))


if __name__ == '__main__':
    pytest.main()

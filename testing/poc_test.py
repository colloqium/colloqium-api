import unittest
from context.context import create_test_app
import io


class TestBlueprint(unittest.TestCase):
    def setUp(self):
        self.app = create_test_app()

    def test_twilio_call(self):
        response = self.app.post('/twilio_call')
        self.assertEqual(response.status_code, 200)

    def test_twilio_message(self):
        response = self.app.post('/twilio_message')
        self.assertEqual(response.status_code, 200)

    def test_index(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)

    def test_interaction(self):
        with open('test_profiles.csv', 'rb') as csv_file:
            csv_data = io.BytesIO(csv_file.read())

        with self.app.test_client() as client:
            response = client.post('/interaction/last_action?last_action=some_value', data={
                'recipient_csv': (csv_data, 'test.csv'),
                'campaign_name': 'GOTV for All',
                'campaign_prompt': 'Encourage the recipient to register to vote. Find out what state they are in so that you can point them to the right website.',
                'campaign_end_date': '2023-11-09',
                'interaction_type': 'text',
                'sender_name': 'GOTV for All',
                'sender_information': 'A nonpartisan nonprofit that supports voter registration and turnout.'
            })
            self.assertEqual(response.status_code, 200)

    def test_call(self):
        response = self.app.post('/call/interaction_id')
        self.assertEqual(response.status_code, 200)

    def test_text_message(self):
        response = self.app.post('/text_message/interaction_id')
        self.assertEqual(response.status_code, 200)

    def test_plan(self):
        response = self.app.post('/plan/recipient_id')
        self.assertEqual(response.status_code, 200)
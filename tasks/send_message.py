from models.interaction import Interaction, InteractionStatus, SenderVoterRelationship
from models.voter import Voter
from models.sender import Sender
from context.apis import twilio_client
from tools.utility import format_phone_number
from context.apis import twilio_messaging_service_sid, message_webhook_url
from context.database import db
from context.analytics import analytics, EVENT_OPTIONS
from context.celery import celery_client
import datetime
from celery.exceptions import MaxRetriesExceededError
from sqlalchemy.exc import OperationalError
from tools.db_utility import check_db_connection
from tasks.base_task import BaseTaskWithDB


@celery_client.task(bind=True, base=BaseTaskWithDB, max_retries=10, default_retry_delay=30)  # bind=True to access self, max_retries and default_retry_delay are optional
def send_message(self, message_body, sender_phone_number, voter_id, sender_id, interaction_id):
    with self.session_scope():
        voter = Voter.query.get(voter_id)
        sender = Sender.query.get(sender_id)
        interaction = Interaction.query.get(interaction_id)

        sender_voter_relationship = SenderVoterRelationship.query.filter_by(sender_id=sender_id, voter_id=voter_id).first()

        #Check if the sender has opted out of contacts
        if sender_voter_relationship.opted_out == True:
            print(f"Recipient has opted out of contacts")
            interaction.interaction_status = InteractionStatus.OPTED_OUT
            db.session.add(interaction)
            db.session.commit()
            return

        print(f"Message called at {datetime.datetime.now()}")
        twilio_client.messages.create(
                    body=message_body,
                    from_=format_phone_number(sender_phone_number),
                    status_callback=message_webhook_url,
                    to=format_phone_number(voter.voter_phone_number),
                    messaging_service_sid=twilio_messaging_service_sid)
        
        analytics.track(voter.id, EVENT_OPTIONS.sent, {
                    'interaction_id': interaction.id,
                    'voter_name': voter.voter_name,
                    'voter_phone_number': format_phone_number(voter.voter_phone_number),
                    'sender_name': sender.sender_name,
                    'sender_phone_number': format_phone_number(sender_phone_number),
                    'message': message_body,
                })

        # if interaction status is less than sent, set it to sent. Do not want to overwrite responses from the voter as "sent status"
        if interaction.interaction_status < InteractionStatus.SENT:
            interaction.interaction_status = InteractionStatus.SENT

        db.session.add(interaction)
        db.session.commit()
        db.session.remove()
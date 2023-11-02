from models.interaction import Interaction, InteractionStatus
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


@celery_client.task(bind=True, max_retries=10, default_retry_delay=30)  # bind=True to access self, max_retries and default_retry_delay are optional
def send_message(self, message_body, sender_phone_number, voter_id, sender_id, interaction_id):
    from context.app import create_app # late import 
    app = create_app()
    print("Sub function to send message called")
    
    try:
        with app.app_context():
            if not check_db_connection(db):
                        print("Database connection failed")
                        # retry in 30 seconds
                        self.retry()

            print("App existed to give app context")
            voter = Voter.query.get(voter_id)
            sender = Sender.query.get(sender_id)
            interaction = Interaction.query.get(interaction_id)

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
    except OperationalError as e:
        try:
            self.retry(exc=e) # retry the task
        except MaxRetriesExceededError:
            print("Max retries exceeded, aborting task")
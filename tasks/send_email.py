from models.interaction import Interaction, InteractionStatus
from models.voter import Voter
from models.sender import Sender
from context.apis import sg
from context.database import db
from context.analytics import analytics, EVENT_OPTIONS
from context.celery import celery_client
import datetime
from tasks.base_task import BaseTaskWithDB
from sendgrid.helpers.mail import Mail


@celery_client.task(bind=True, base=BaseTaskWithDB, max_retries=10, default_retry_delay=30)  # bind=True to access self, max_retries and default_retry_delay are optional
def send_email(self, email_subject, email_body, sender_email, voter_id, sender_id, interaction_id):
    with self.session_scope():
        voter = Voter.query.get(voter_id)
        sender = Sender.query.get(sender_id)
        interaction = Interaction.query.get(interaction_id)

        message = Mail(
            from_email=sender_email,
            to_emails=voter.voter_email,
            subject=email_subject,
            html_content=email_body
        )

        print(f"Email called at {datetime.datetime.now()}")
        response = sg.send(message)


        
        analytics.track(voter.id, EVENT_OPTIONS.sent, {
                    'interaction_id': interaction.id,
                    'voter_name': voter.voter_name,
                    'voter_email': voter.voter_email,
                    'sender_name': sender.sender_name,
                    'sender_email': sender_email,
                    'email': email_body,
                    'response_body': response.body,
                    'response_status_code': response.status_code,
                    'response_headers': response.headers,
                })

        # if interaction status is less than sent, set it to sent. Do not want to overwrite responses from the voter as "sent status"
        if interaction.interaction_status < InteractionStatus.SENT:
            interaction.interaction_status = InteractionStatus.SENT

        db.session.add(interaction)
        db.session.commit()
        db.session.remove()
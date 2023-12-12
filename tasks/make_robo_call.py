from models.interaction import Interaction, InteractionStatus
from models.voter import Voter
from models.sender import Sender
from context.apis import twilio_client
from tools.utility import format_phone_number
from context.apis import message_webhook_url
from context.database import db
from context.analytics import analytics, EVENT_OPTIONS
from context.celery import celery_client
import datetime
from logs.logger import logger
from tasks.base_task import BaseTaskWithDB
from twilio.twiml.voice_response import VoiceResponse, Say, Record


@celery_client.task(bind=True, base=BaseTaskWithDB, max_retries=10, default_retry_delay=30)  # bind=True to access self, max_retries and default_retry_delay are optional
def make_robo_call_task(self, call_script, sender_phone_number, voter_id, sender_id, interaction_id):
    with self.session_scope():
        voter = Voter.query.get(voter_id)
        sender = Sender.query.get(sender_id)
        interaction = Interaction.query.get(interaction_id)

        # create a twilio xml with the body of the call_script
        twilio_xml = VoiceResponse()
        twilio_xml.say(call_script)
        twilio_xml.record()
        twilio_xml.hangup() 


        logger.debug(f"robo_call called at {datetime.datetime.now()}")
        twilio_client.calls.create(
                    twiml=twilio_xml,
                    from_=format_phone_number(sender_phone_number),
                    status_callback=message_webhook_url,
                    to=format_phone_number(voter.voter_phone_number))
        
        analytics.track(voter.id, EVENT_OPTIONS.sent, {
                    'interaction_id': interaction.id,
                    'voter_name': voter.voter_name,
                    'voter_phone_number': format_phone_number(voter.voter_phone_number),
                    'sender_name': sender.sender_name,
                    'sender_phone_number': format_phone_number(sender_phone_number),
                    'message': call_script,
                })

        # if interaction status is less than sent, set it to sent. Do not want to overwrite responses from the voter as "sent status"
        if interaction.interaction_status < InteractionStatus.SENT:
            interaction.interaction_status = InteractionStatus.SENT

        db.session.add(interaction)
        db.session.commit()
        db.session.remove()
# import Flask and other libraries
from models.interaction import InteractionStatus
from models.voter import Voter
from models.sender import Sender
# from logs.logger import logging
from context.database import db
from context.analytics import analytics, EVENT_OPTIONS
from logs.logger import logger
from sqlalchemy.exc import OperationalError
from context.celery import celery_client
from tools.db_utility import check_db_connection
from models.interaction import Interaction
from celery.exceptions import MaxRetriesExceededError


@celery_client.task(bind=True, max_retries=10, default_retry_delay=30)  # bind=True to access self, max_retries and default_retry_delay are optional
def process_twilio_callback(self, interaction_id, status, phone_number):
    from context.app import create_app # late import 
    app = create_app()
    print("Sub function to send message called")
    
    try:
        with app.app_context():
            try:
                if not check_db_connection(db):
                    print("Database connection failed")
                    # retry in 30 seconds
                    self.retry()

                interaction = Interaction.query.filter_by(id=interaction_id).first()
                 
                # update the interaction status
                if status == 'sent':
                    print("Message sent")
                    if interaction.interaction_status < InteractionStatus.SENT:
                        interaction.interaction_status = InteractionStatus.SENT
                if status == 'delivered':
                    print("Message delivered")
                    if interaction.interaction_status < InteractionStatus.DELIVERED:
                        interaction.interaction_status = InteractionStatus.DELIVERED

                voter = Voter.query.filter_by(id=interaction.voter_id).first()
                sender = Sender.query.filter_by(id=interaction.sender_id).first()

                analytics.track(voter.id, EVENT_OPTIONS.interaction_call_back, {
                            'status': status,
                            'interaction_id': interaction.id,
                            'interaction_type': interaction.interaction_type,
                            'voter_name': voter.voter_name,
                            'voter_phone_number': voter.voter_phone_number,
                            'sender_name': sender.sender_name,
                            'sender_phone_number': phone_number.get_full_phone_number(),
                        })
                
                db.session.add(interaction)
                db.session.commit()

            finally:
                db.session.close_all()
    except OperationalError as e:
        try:
            self.retry(exc=e) # retry the task
        except MaxRetriesExceededError:
            print("Max retries exceeded, aborting task")
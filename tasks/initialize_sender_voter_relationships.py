# import Flask and other libraries
# from logs.logger import logging
from context.database import db
from context.celery import celery_client
from tasks.base_task import BaseTaskWithDB
from typing import List
from models.interaction import SenderVoterRelationship


@celery_client.task(bind=True, base=BaseTaskWithDB, max_retries=10, default_retry_delay=30)  # bind=True to access self, max_retries and default_retry_delay are optional
def initialize_sender_voter_relationships(self, sender_id: int, voter_ids: List[int]):
    with self.session_scope():
        for voter_id in voter_ids:
            relationship = SenderVoterRelationship.query.filter_by(sender_id=sender_id, voter_id=voter_id).first()
            if not relationship:
                relationship = SenderVoterRelationship(sender_id=sender_id, voter_id=voter_id)
                db.session.add(relationship)
        db.session.commit()
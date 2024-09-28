from context.database import db
from context.celery import celery_client
from tasks.base_task import BaseTaskWithDB
from models.voter import Voter, VoterProfile
from tools.utility import format_phone_number
from context.analytics import analytics, EVENT_OPTIONS
from flask import jsonify
from typing import List

@celery_client.task(bind=True, base=BaseTaskWithDB, max_retries=10, default_retry_delay=30)
def create_or_update_voters(self, voters: List[Voter]):
    with self.session_scope():
        for voter in voters:
            voter_name = voter.get('voter_name')
            voter_phone_number = voter.get('voter_phone_number')
            voter_email = voter.get('voter_email')

            cleaned_phone_number = format_phone_number(voter_phone_number) if voter_phone_number else None

            # Find existing voter by name and phone/email
            existing_voter = Voter.query.filter_by(
                voter_name=voter_name,
                voter_phone_number=cleaned_phone_number
            ).first()

            if not existing_voter and voter_email:
                existing_voter = Voter.query.filter_by(
                    voter_name=voter_name,
                    voter_email=voter_email
                ).first()

            # Create a new voter if one does not exist
            if not existing_voter:
                new_voter = Voter(
                    voter_name=voter_name,
                    voter_phone_number=cleaned_phone_number,
                    voter_email=voter_email
                )

                db.session.add(new_voter)
                db.session.commit()
                existing_voter = new_voter

            if not existing_voter:
                return jsonify({'error': 'Voter could not be found or created', 'status_code': 500}), 500

            voter_profile_data = voter.get('voter_profile')

            if voter_profile_data:
                # Check if VoterProfile already exists
                profile_object = VoterProfile.query.filter_by(voter_id=existing_voter.id).first()

                if not profile_object:
                    # Create new VoterProfile
                    profile_object = VoterProfile(voter_id=existing_voter.id)
                    db.session.add(profile_object)

                # Update VoterProfile attributes
                profile_object.interests = voter_profile_data.get('interests')
                profile_object.policy_preferences = voter_profile_data.get('policy_preferences')
                profile_object.preferred_contact_method = voter_profile_data.get('preferred_contact_method')

                db.session.commit()

            analytics.track(existing_voter.id, EVENT_OPTIONS.voter_created_or_updated, {
                'name': existing_voter.voter_name,
                'phone': existing_voter.voter_phone_number,
                'email': existing_voter.voter_email
            })

            print(f"Voter {existing_voter.id} created or updated")
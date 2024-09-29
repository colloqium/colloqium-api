from context.database import db
from context.celery import celery_client
from tasks.base_task import BaseTaskWithDB
from models.voter import Voter, VoterProfile
from models.sender import Audience, Campaign
from tools.utility import format_phone_number
from context.analytics import analytics, EVENT_OPTIONS
from flask import jsonify
from typing import List

@celery_client.task(bind=True, base=BaseTaskWithDB, max_retries=10, default_retry_delay=30)
def create_or_update_voters(self, voters: List[Voter], audience_data=None):
    with self.session_scope():
        voter_ids = []
        print(f"Creating or updating {len(voters)} voters")
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

            voter_ids.append(existing_voter.id)
        
        print(f"Finished creating or updating voters. Total voters: {len(voter_ids)}")

        if audience_data:
            print(f"Creating or updating audience")
            # After voters are created, update or create the audience
            audience = Audience.query.filter_by(
                audience_name=audience_data['audience_name'],
                sender_id=audience_data['sender_id']
            ).first()
            
            if not audience:
                audience = Audience(
                    audience_name=audience_data['audience_name'],
                    audience_information=audience_data.get('audience_information'),
                    sender_id=audience_data['sender_id']
                )
                db.session.add(audience)
            
            # Fetch voters by IDs and associate them with the audience
            new_voters = Voter.query.filter(Voter.id.in_(voter_ids)).all()
            audience.voters.extend(new_voters)
            
            # Associate campaigns if provided
            if 'campaigns' in audience_data:
                campaigns = Campaign.query.filter(Campaign.id.in_(audience_data['campaigns'])).all()
                audience.campaigns.extend(campaigns)

            print(f"Audience {audience.id} created or updated")
            print(f"Audience: {audience}")

            db.session.commit()

        analytics.track(existing_voter.id, EVENT_OPTIONS.voter_created_or_updated, {
            'name': existing_voter.voter_name,
            'phone': existing_voter.voter_phone_number,
            'email': existing_voter.voter_email
        })

        print(f"Voter {existing_voter.id} created or updated")
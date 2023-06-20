from flask import redirect, request, Blueprint, url_for
# import Flask and other libraries
from flask import render_template
from models.models import Interaction, InteractionStatus, Sender
from context.constants import INTERACTION_TYPES
# from logs.logger import logger
# Import the functions from the other files

confirm_message_bp = Blueprint('confirm_messages', __name__)

@confirm_message_bp.route("/<int:sender_id>/confirm_messages", methods=['GET', 'POST'])
def confirm_messages(sender_id):
    # look for interactions with the sender_id and an interaction status InteractionStatus.INITIALIZED
    interactions = Interaction.query.filter_by(sender_id=sender_id, interaction_status=InteractionStatus.INITIALIZED).all() 

    #get the sender object that matches the sender_id
    sender = Sender.query.get(sender_id)

    if sender is None:
        print(f"Sender with sender_id {sender_id} does not exist")
        #reroute to the interaction page with an error message
        print("Redirecting to interaction page with error message")
        return redirect(url_for('bp.interaction', last_action='sender_not_found'))

    # log the name of the sender and the number of interactions to be confirmed
    print(f"Sender {sender.sender_name} has {len(interactions)} interactions to confirm")

    return render_template('confirm_message.html',
                           interactions=interactions, interaction_types=INTERACTION_TYPES)
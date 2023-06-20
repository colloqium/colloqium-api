from flask import Blueprint
# import Flask and other libraries
from flask import render_template, redirect, url_for, session
from forms.interaction_form import InteractionForm
from models.models import Recipient, Sender, Interaction
# from logs.logger import logger
from context.database import db
from context.apis import client, call_webhook_url, twilio_number

call_bp = Blueprint('call', __name__)

@call_bp.route("/call/<interaction_id>", methods=['POST', 'GET'])
def call(interaction_id):
    try:
        recipient_call = Interaction.query.get(session['interaction_id'])
        recipient = Recipient.query.get(recipient_call.recipient_id)
        sender = Sender.query.get(recipient_call.sender_id)

        # Clear the session data now that we're done with it
        if 'interaction_id' in session:
            del session['interaction_id']

        print(
            f"Starting call with system prompt '{recipient_call.conversation[0].get('content')}' and user number '{recipient.recipient_phone_number}'"
        )

        # Start a new call
        call = client.calls.create(url=call_webhook_url,
                                   to=recipient.recipient_phone_number,
                                   from_=twilio_number)

        print(f"Started call with SID '{call.sid}'")

        #add call.sid to recipient_call
        recipient_call.twilio_conversation_sid = call.sid
        db.session.commit()

        return redirect(
            url_for('bp.interaction',
                    last_action="Calling" + recipient.recipient_name + "for" +
                    sender.sender_name))

    except Exception as e:
        print(f"Exception occurred: {e}", exc_info=True)
        return render_template('interaction.html',
                               form=InteractionForm(),
                               last_action="Error")

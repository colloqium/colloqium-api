from flask import Blueprint
# import Flask and other libraries
from flask import render_template, jsonify
from forms.interaction_form import InteractionForm
from models.models import Recipient, Interaction
from logs.logger import logger, logging
from context.database import db
from context.apis import client, twilio_number

text_message_bp = Blueprint('text_message', __name__)


@text_message_bp.route("/text_message/<interaction_id>", methods=['POST'])
def text_message(interaction_id):
    try:
        text_thread = db.session.query(Interaction).get(interaction_id)

        if text_thread:
            recipient = Recipient.query.get(text_thread.recipient_id)
            conversation = text_thread.conversation

            logging.debug(
                f"Texting route recieved Conversation: {conversation}")

            body = conversation[-1].get('content')

            logger.info(
                f"Starting text message with body'{body}' and user number '{recipient.recipient_phone_number}'"
            )

            # Start a new text message thread
            text_message = client.messages.create(
                body=body,
                from_=twilio_number,
                to=recipient.recipient_phone_number)

            logging.info(
                f"Started text Conversation with recipient '{recipient.recipient_name}' on text SID '{text_message.sid}'"
            )

            db.session.commit()

            return jsonify({
                'status': 'success',
                'last_action':
                f"Sending text to {recipient.recipient_name} at {recipient.recipient_phone_number}",
                'First Message': body,
                'conversation': text_thread.conversation
            }), 200

        return jsonify({
            'status':
            'error',
            'last_action':
            f"Error Sending text to with interaction id {interaction_id}"
        }), 400

    except Exception as e:
        logger.error(f"Exception occurred: {e}", exc_info=True)
        return render_template('interaction.html',
                               form=InteractionForm(),
                               last_action="Error")


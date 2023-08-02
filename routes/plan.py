
from flask import Blueprint
# import Flask and other libraries
from flask import session, jsonify
from models.models import Interaction
from tools.campaign_agent_tools import CampaignTools, extract_action, execute_action
from tools.utility import add_message_to_conversation, get_llm_response_to_conversation
# from logs.logger import logger, logging
from context.database import db

plan_bp = Blueprint('plan', __name__)


@plan_bp.route("/plan/<int:recipient_id>", methods=['GET', 'POST'])
def plan(recipient_id):
    try:
        interaction = Interaction.query.get(session['interaction_id'])
        recipient = interaction.recipient

        most_recent_message = interaction.conversation[-1].get('content')

        print(f"Creating plan for {recipient.recipient_name}")
        print(f"Conversation so far: {interaction.conversation}")
        print(f"Most Recent Message {most_recent_message}")

        # Instantiate campaign tools
        campaign_tools = CampaignTools(interaction, db)

        # Maximum iterations to avoid infinite loop
        max_iterations = 10
        iteration = 0

        # Execute action based on the recent message
        while True:
            iteration += 1

            if 'Action' in most_recent_message:
                action_name, action_params = extract_action(
                    most_recent_message)
                action_result = execute_action(campaign_tools, action_name,
                                               action_params)
                most_recent_message = f"Observation: {action_result}"
                add_message_to_conversation(interaction.conversation, most_recent_message)

            most_recent_message = get_llm_response_to_conversation(interaction.conversation)

            # Update conversation with the latest response
            add_message_to_conversation(interaction.conversation, most_recent_message)

            # flush the logs
            for handler in logging.getLogger().handlers:
                handler.flush()

            if ('WAIT' in most_recent_message.upper()) or (iteration >=
                                                           max_iterations):
                if iteration >= max_iterations:
                    most_recent_message = "Observation: The conversation exceeded the maximum number of iterations without reaching a 'WAIT' state. The conversation will be paused here, and will need to be reviewed."
                    add_message_to_conversation(interaction.conversation,
                                                most_recent_message)
                break

        db.session.commit()
        return jsonify({
            'status': 'success',
            'last_action': 'Planning for ' + recipient.recipient_name,
            'conversation': interaction.conversation
        }), 200

    except Exception as e:
        print(f"Exception occurred: {e}", exc_info=True)
        return jsonify({'status': 'error', 'last_action': 'Error'}), 500
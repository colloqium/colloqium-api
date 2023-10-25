from tools.ai_functions.ai_function import AIFunction, FunctionProperty
from models.interaction import Interaction
from models.sender import Sender
from models.ai_agents.agent import Agent
from sqlalchemy.orm.attributes import flag_modified
from context.database import db
from context.apis import client, twilio_messaging_service_sid, message_webhook_url
from tools.utility import format_phone_number
from tools.ai_functions.send_message import SendMessage


campaign_id = FunctionProperty(name="campaign_id", paramater_type="string", description="The ID of the outreach campaign this agent is texting for")
voter_id = FunctionProperty(name="voter_id", paramater_type="string", description="The ID of the voter this agent is texting")
inbound_message = FunctionProperty(name="inbound_message", paramater_type="string", description="The message the voter sent")
alert_message = FunctionProperty(name="alert_message", paramater_type="string", description="The message to send to the campaign manager")
voter_message = FunctionProperty(name="voter_message", paramater_type="string", description="The message to send back to the voter when the campaign manager is alerted")

class AlertCampaignManager(AIFunction):
    
  def __init__(self, name="alert_campaign_manager",description="Send an alert to the campaign manager that something needs their attention, like if they need to follow up with someone. Also prepars a message for the voter to send back to them.", parameters=[campaign_id, voter_id, alert_message, inbound_message, voter_message]):
    super().__init__(name,description,parameters)

  def call(self, **kwargs):
    print("Calling AlertCampaignManager")
    print(kwargs)

    # check for required parameters
    if not kwargs.get("campaign_id"):
      return "Campaign ID is required"
    
    if not kwargs.get("voter_id"):
      return "Voter ID is required"
    
    if not kwargs.get("alert_message"):
      return "Alert message is required"
    
    if not kwargs.get("inbound_message"):
      return "Inbound message is required"
    
    if not kwargs.get("voter_message"):
      return "Voter message is required"
    
    # unpack paramaters to variables
    campaign_id = kwargs["campaign_id"]
    voter_id = kwargs["voter_id"]
    inbound_message = kwargs["inbound_message"]
    alert_message = kwargs["alert_message"]
    voter_message = kwargs["voter_message"]

    # get the interaction associated with this texting agent, campaign, and voter
    print(f"Looking for an interaction with campaign_id {campaign_id} and voter_id {voter_id}")
    interaction = Interaction.query.filter_by(campaign_id=campaign_id, voter_id=voter_id).first()
    
    # do a query for an agent with the interaction in it's interactions list and the name "texting_agent"
    texting_agent = Agent.query.filter(Agent.interactions.any(id=interaction.id), Agent.name == "texting_agent").first()

    if not interaction:
        return "No interaction found for this campaign and voter"

    interaction.conversation = texting_agent.conversation_history.copy()

    flag_modified(interaction, "conversation")

    # save the interaction and texting agent
    db.session.add(interaction)
    db.session.add(texting_agent)
    db.session.commit()
    ()

    #send text to sender's alert phone number
    sender_id = interaction.campaign.sender_id
    sender = Sender.query.filter_by(id=sender_id).first()
    voter = interaction.voter

    # check if the sender alert phone number is set, if not, return a message with the last message and let the agent know that the campaign manager was not alerted
    if not sender.alert_phone_number:
        return f"Sender {sender.sender_name} does not have an alert phone number set. They will be notified later. The agent has written the following message to send back to the voter {voter_message}"
    
    message = f'''Voter {voter.voter_name} has a question for you. You can reach them at {voter.voter_phone_number}.

    The alert message is:
    {alert_message}
    
    They voter said:
    {inbound_message}.
    
    The agent has sent them the following message in the meantime {voter_message}'''

    phone_number = interaction.select_phone_number()
    alert_phone_number = format_phone_number(sender.alert_phone_number)

    if phone_number is None:
        return "Error: Phone number from interaction is None"

    if alert_phone_number is None or sender.alert_phone_number is None:
        return "Error: Alert phone number from sender is None"
    

    print(f"Sending alert message to campaign manager: {message}")

    client.messages.create(
        body=message,
        from_=phone_number,
        status_callback=message_webhook_url,
        to=alert_phone_number,
        messaging_service_sid=twilio_messaging_service_sid
    )

    return f"Campaign Manager alerted and message sent to voter"


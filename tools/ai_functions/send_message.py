from tools.ai_functions.ai_function import AIFunction, FunctionProperty
from models.interaction import Interaction, InteractionStatus
from models.voter import Voter
from models.sender import Sender
from context.apis import client
from tools.utility import format_phone_number
from context.apis import twilio_messaging_service_sid, message_webhook_url
from context.database import db
from context.analytics import analytics, EVENT_OPTIONS
import datetime
from context.scheduler import scheduler
from flask import current_app

'''
{
        "name": "send_message",
        "description": "send a message with the agent previously created for this campaign and voter. Will send an notification back to the planner when the message is sent.",
        "parameters": {
          "type": "object",
          "properties": {
            "campaign_id": {
              "type": "string",
              "description": "The ID of the outreach campaign this agent is texting for"
            },
            "voter_id": {
              "type": "string",
              "description": "The ID of the voter this agent is texting"
            },
            "time_to_send": {
              "type": "datetime",
              "description": "The time to send the message"
            },
            "outbound_message": {
              "type": "string",
              "description": "The message to send to the voter"
            }
          },
          "required": ["campaign_id", "voter_id", "outbound_message"]
        }
    }
'''

campaign_id = FunctionProperty(name="campaign_id", paramater_type="string", description="The ID of the outreach campaign this agent is texting for")
voter_id = FunctionProperty(name="voter_id", paramater_type="string", description="The ID of the voter this agent is texting")
outbound_message = FunctionProperty(name="outbound_message", paramater_type="string", description="The message to send to the voter. This should always be a short text message, do not put other function reults in here.")

class SendMessage(AIFunction):

  def __init__(self, name="send_message",description="send a message with the agent previously created for this campaign and voter. Will send an notification back to the planner when the message is sent.", parameters=[campaign_id, voter_id, outbound_message]):
    super().__init__(name, description, parameters)

  def call(self, **kwargs):
      print("Calling SendMessage")
      print(kwargs)

      #check if the required arguments are included
      if "campaign_id" not in kwargs.keys():
          return "Missing required argument: campaign_id"
      if "voter_id" not in kwargs.keys():
          return "Missing required argument: voter_id"
      if "outbound_message" not in kwargs.keys():
          return "Missing required argument: outbound_message"
      
      # unpack paramaters to variables
      campaign_id = kwargs["campaign_id"]
      voter_id = kwargs["voter_id"]
      outbound_message = kwargs["outbound_message"]
      
      interaction = Interaction.query.filter_by(campaign_id=campaign_id, voter_id=voter_id).first()

      sender_phone_number = interaction.select_phone_number()

      #start the scheduler if it is not already running
      if not scheduler.running:
          print("Starting scheduler")
          scheduler.start()
      
      # schedule this message to send in 15 seconds
      scheduler.add_job(self.send_message, 'date', run_date=datetime.datetime.now() + datetime.timedelta(seconds=5), args=[outbound_message, sender_phone_number, voter_id, interaction.sender.id, interaction.id, current_app._get_current_object()], misfire_grace_time=20)

      #check the scheduler for the job we just added
      print(f"Scheduler jobs: {scheduler.get_jobs()}")

      db.session.add(interaction)
      db.session.commit()
      db.session.close()

      return "Message sent successfully. Wait for a response from the voter or a new request from the campaign. Say Ok, if you understand."
  
  def send_message(self, message_body, sender_phone_number, voter_id, sender_id, interaction_id, app):

    print("Sub function to send message called")
    
    try:
      with app.app_context():
          print("App existed to give app context")
          voter = Voter.query.get(voter_id)
          sender = Sender.query.get(sender_id)
          interaction = Interaction.query.get(interaction_id)

          print(f"Message called at {datetime.datetime.now()}")
          client.messages.create(
                      body=message_body,
                      from_=format_phone_number(sender_phone_number),
                      status_callback=message_webhook_url,
                      to=format_phone_number(voter.voter_phone_number),
                      messaging_service_sid=twilio_messaging_service_sid)
          
          analytics.track(voter.id, EVENT_OPTIONS.sent, {
                      'interaction_id': interaction.id,
                      'voter_name': voter.voter_name,
                      'voter_phone_number': format_phone_number(voter.voter_phone_number),
                      'sender_name': sender.sender_name,
                      'sender_phone_number': format_phone_number(sender_phone_number),
                      'message': message_body,
                  })

          # if interaction status is less than sent, set it to sent. Do not want to overwrite responses from the voter as "sent status"
          if interaction.interaction_status < InteractionStatus.SENT:
              interaction.interaction_status = InteractionStatus.SENT
    except Exception as e:
       print(f"Error in send_message sub-function: {e}")
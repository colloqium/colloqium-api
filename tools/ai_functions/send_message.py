from tools.ai_functions.ai_function import AIFunction, FunctionProperty
from models.interaction import Interaction
from context.database import db
from tasks.send_message import send_message

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

      send_message.apply_async(args=[outbound_message, sender_phone_number, voter_id, interaction.sender.id, interaction.id], countdown=10)

      db.session.add(interaction)
      db.session.commit()

      return "Message sent successfully. Wait for a response from the voter or a new request from the campaign. Say Ok, if you understand."
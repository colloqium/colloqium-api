from tools.ai_functions.ai_function import AIFunction, FunctionProperty
from models.interaction import Interaction
from context.database import db
from tasks.send_email import send_email

'''
{
        "name": "send_email",
        "description": "send a email with the agent previously created for this campaign and voter. Will send an notification back to the planner when the email is sent.",
        "parameters": {
          "type": "object",
          "properties": {
            "campaign_id": {
              "type": "string",
              "description": "The ID of the outreach campaign this agent is emailing for"
            },
            "voter_id": {
              "type": "string",
              "description": "The ID of the voter this agent is emailing"
            },
            "time_to_send": {
              "type": "datetime",
              "description": "The time to send the email"
            },
            "email_subject": {
              "type": "string",
              "description": "The subject of the email"
            },
            "email_body": {
                "type": "string",
                "description": "The body of the email"
            }
          },
          "required": ["campaign_id", "voter_id", "email_subject", "email_body"]
        }
    }
'''

campaign_id = FunctionProperty(name="campaign_id", paramater_type="string", description="The ID of the outreach campaign this agent is emailing for")
voter_id = FunctionProperty(name="voter_id", paramater_type="string", description="The ID of the voter this agent is emailing")
email_subject = FunctionProperty(name="email_subject", paramater_type="string", description="The subject of the email we will send to the voter, do not put other function reults in here.")
email_body = FunctionProperty(name="email_body", paramater_type="string", description="The body of the email we will send to the voter, do not put other function reults in here.")

class SendEmail(AIFunction):

  def __init__(self, name="send_email",description="send an email with the agent previously created for this campaign and voter. Will send an notification back to the planner when the email is sent.", parameters=[campaign_id, voter_id, email_subject, email_body]):
    super().__init__(name, description, parameters)

  def call(self, **kwargs):
      print("Calling SendEmail")
      print(kwargs)

      #check if the required arguments are included
      if "campaign_id" not in kwargs.keys():
          return "Missing required argument: campaign_id"
      if "voter_id" not in kwargs.keys():
          return "Missing required argument: voter_id"
      if "email_subject" not in kwargs.keys():
          return "Missing required argument: email_subject"
      if "email_body" not in kwargs.keys():
          return "Missing required argument: email_body"
      
      # unpack paramaters to variables
      campaign_id = kwargs["campaign_id"]
      voter_id = kwargs["voter_id"]
      email_subject = kwargs["email_subject"]
      email_body = kwargs["email_body"]
      
      interaction = Interaction.query.filter_by(campaign_id=campaign_id, voter_id=voter_id).first()

      sender_email = interaction.select_email()

      send_email.apply_async(args=[email_subject, email_body, sender_email, voter_id, interaction.sender.id, interaction.id], countdown=10)

      db.session.add(interaction)
      db.session.commit()

      return "Email sent successfully. Wait for a response from the voter or a new request from the campaign. Say Ok, if you understand."
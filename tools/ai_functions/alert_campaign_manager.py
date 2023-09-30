from tools.ai_functions.ai_function import AIFunction, FunctionProperty

'''
{
        "name": "alert_campaign_manager",
        "description": "Send an alert to the campaign manager that something needs their attention. Typically a question from the voter that the agent cannot answer.",
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
            "alert_message": {
              "type": "string",
              "description": "The message to send to the campaign manager"
            }
          },
          "required": ["campaign_id", "voter_id", "alert_message"]
        }
    }
'''

campaign_id = FunctionProperty(name="campaign_id", type="int", description="The ID of the outreach campaign this agent is texting for")
voter_id = FunctionProperty(name="voter_id", type="int", description="The ID of the voter this agent is texting")
alert_message = FunctionProperty(name="alert_message", type="string", description="The message to send to the campaign manager")

class AlertCampaignManager(AIFunction):
    
        def __init__(self):
            super().__init__(name="alert_campaign_manager",description="Send an alert to the campaign manager that something needs their attention. Typically a question from the voter that the agent cannot answer.", parameters=[campaign_id, voter_id, alert_message])
    
        def call(self, **kwargs):
            print("Calling AlertCampaignManager")
            print(kwargs)
            return
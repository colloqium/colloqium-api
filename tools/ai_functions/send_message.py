from ai_functions import AIFunction, FunctionProperty


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
            "outbound_message": {
              "type": "string",
              "description": "The message to send to the voter"
            }
          },
          "required": ["campaign_id", "voter_id", "outbound_message"]
        }
    }
'''

campaign_id = FunctionProperty(name="campaign_id", required=True, description="The ID of the outreach campaign this agent is texting for")
voter_id = FunctionProperty(name="voter_id", required=True, description="The ID of the voter this agent is texting")
outbound_message = FunctionProperty(name="outbound_message", required=True, description="The message to send to the voter")

class SendMessage(AIFunction):

    def __init__(self):
        super().__init__(name="send_message",description="send a message with the agent previously created for this campaign and voter. Will send an notification back to the planner when the message is sent.", parameters=[campaign_id, voter_id, outbound_message])

    def call(self, **kwargs):
        print("Calling SendMessage")
        print(kwargs)
        return
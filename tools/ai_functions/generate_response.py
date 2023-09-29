from ai_functions import AIFunction, FunctionProperty

'''
{
        "name": "generate_response",
        "description": "generate a response with the agent previously created for this campaign and voter. Will send an notification back to the planner when the message is prepared.",
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
            "inbound_message": {
              "type": "string",
              "description": "The message received from the voter"
            }
          },
          "required": ["campaign_id", "voter_id", "inbound_message"]
        }
    }
'''

campaign_id = FunctionProperty(name="campaign_id", required=True, description="The ID of the outreach campaign this agent is texting for")
voter_id = FunctionProperty(name="voter_id", required=True, description="The ID of the voter this agent is texting")
inbound_message = FunctionProperty(name="inbound_message", required=True, description="The message received from the voter")


class GenerateResponse(AIFunction):

    def __init__(self):
        super().__init__(name="generate_response",description="generate a response with the agent previously created for this campaign and voter. Will send an notification back to the planner when the message is prepared.", parameters=[campaign_id, voter_id, inbound_message])

    def call(self, **kwargs):
        print("Calling GenerateResponse")
        print(kwargs)
        return
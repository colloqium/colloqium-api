from ai_functions import AIFunction, FunctionProperty

'''
{
      "name": "create_texting_agent",
      "description": "Spin up an volunteer texting agent to text the voter. Initializes the first message in the conversation. Will send an notification back to the planner when the message is prepared to be sent.",
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
          }
        },
        "required": ["campaign_id", "voter_id"]
      }
    }
'''

campaign_id = FunctionProperty(name="campaign_id", required=True, description="The ID of the outreach campaign this agent is texting for")
voter_id = FunctionProperty(name="voter_id", required=True, description="The ID of the voter this agent is texting")


class CreateTextingAgent(AIFunction):

    def __init__(self):
        super().__init__(name="create_texting_agent",description="Spin up an volunteer texting agent to text the voter. Initializes the first message in the conversation. Will send an notification back to the planner when the message is prepared to be sent.", parameters=[campaign_id, voter_id])

    def call(self, **kwargs):
        print("Calling CreateTextingAgent")
        print(kwargs)
        return
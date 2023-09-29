from ai_function import AIFunction, FunctionProperty


'''
{
        "name": "end_conversation",
        "description": "End the conversation with the votera and do not send a response. Can end either because no response needed or if voter mentions violence or other inappropriate content.",
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
                "ending_reason": {
                    "type": "string",
                    "description": "The reason the conversation is ending"
                }
            },
            "required": ["campaign_id", "voter_id", "ending_reason"]
        }
    }
'''

campaign_id = FunctionProperty(name="campaign_id", required=True, description="The ID of the outreach campaign this agent is texting for")
voter_id = FunctionProperty(name="voter_id", required=True, description="The ID of the voter this agent is texting")
ending_reason = FunctionProperty(name="ending_reason", required=True, description="The reason the conversation is ending")

class EndConversation(AIFunction):

    def __init__(self):
        super().__init__(name="end_conversation",description="End the conversation with the votera and do not send a response. Can end either because no response needed or if voter mentions violence or other inappropriate content.", parameters=[campaign_id, voter_id, ending_reason])

    def call(self, **kwargs):
        print("Calling EndConversation")
        print(kwargs)
        return
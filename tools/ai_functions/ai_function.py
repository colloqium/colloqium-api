
from typing import List
from dataclasses import dataclass

@dataclass
class FunctionProperty:
    name: str # name of the property
    type: str # type of the property
    description: str # description of the property so the agent can know what it does and how to use it

class AIFunction():

    name: str # name of the function
    description: str # description of the function so the agent can know what it does and decide whether to use it
    parameters: List[FunctionProperty] # parameters of the function so the agent can know what it needs to run the function
    schema: str # schema of the function so the agent can know what it needs to run the function includes name description and paramaters

    def __init__(self, name, description, parameters):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.schema = self.get_schema()
    
    def call(self, **kwargs):
        raise NotImplementedError("This function has not been implemented yet")
    
    def get_schema(self):

        '''
        Build a schema to match this format but based on this objects paramaters:

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
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {parameter.name: {"type": parameter.type, "description": parameter.description} for parameter in self.parameters},
                "required": [parameter.name for parameter in self.parameters]
            }
        }
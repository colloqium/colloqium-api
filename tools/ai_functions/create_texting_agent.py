from tools.ai_functions.ai_function import AIFunction, FunctionProperty
from models.ai_agents.texting_agent import TextingAgent
from context.database import db
from dataclasses import dataclass

interaction_id = FunctionProperty(name="interaction_id", paramater_type="string", description="The ID of the interaction this agent is texting for")

@dataclass
class CreateTextingAgent(AIFunction):

    def __init__(self, name="create_texting_agent",description="Spin up an volunteer texting agent to text the voter. Initializes the first message in the conversation. Will send an notification back to the planner when the message is prepared to be confirmed by a human.", parameters=[interaction_id]):
        super().__init__(name,description,parameters)

    def call(self, **kwargs):
        print("Calling CreateTextingAgent")
        print(kwargs)

        # check if the arguments include interaction_id
        if "interaction_id" not in kwargs.keys():
            return "Missing required argument: interaction_id"
        
        # create a new texting agent
        texting_agent = TextingAgent(interaction_id=kwargs["interaction_id"])

        print(f"Succesfully created texting agent: {texting_agent}")

        # get the first response from the agent
        result = texting_agent.last_message().get("content")

        try:
          db.session.add(texting_agent)
          db.session.commit()
          db.session.close()
        except Exception as e:
            return "Was not able to create the agent."

        return "Agent created successfully and initialized first message. Waiting for the message to be human confirmed."
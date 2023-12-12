from tools.ai_functions.ai_function import AIFunction, FunctionProperty
from models.ai_agents.robo_caller_agent import RoboCallerAgent
from context.database import db
from dataclasses import dataclass
from logs.logger import logger

interaction_id = FunctionProperty(name="interaction_id", paramater_type="string", description="The ID of the interaction this agent is texting for")

@dataclass
class CreateRoboCallerAgent(AIFunction):

    def __init__(self, name="create_robo_caller_agent",description="Spin up an volunteer to leave a Robo Call for the voter. Writes the call script and prepares the call to be sent. Will send an notification back to the planner when the call is prepared to be confirmed by a human.", parameters=[interaction_id]):
        super().__init__(name,description,parameters)

    def call(self, **kwargs):
        logger.info("Calling CreateRoboCallerAgent")
        logger.debug(kwargs)

        # check if the arguments include interaction_id
        if "interaction_id" not in kwargs.keys():
            return "Missing required argument: interaction_id"
        
        # create a new RoboCaller Agent
        robo_caller_agent = RoboCallerAgent(interaction_id=kwargs["interaction_id"])

        print(f"Succesfully created RoboCaller Agent: {robo_caller_agent}")

        # get the robo-call script from the agent
        result = robo_caller_agent.last_message().get("content")

        try:
          db.session.add(robo_caller_agent)
          db.session.commit()
        except Exception as e:
            return "Was not able to create the robo-call agent."

        return "Robo-call agent created successfully and initialized script. Waiting for the call to be human confirmed."
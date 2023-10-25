from tools.ai_functions.ai_function import AIFunction, FunctionProperty
from models.interaction import SenderVoterRelationship, Interaction, InteractionStatus
from models.sender import Campaign
from models.ai_agents.texting_agent import TextingAgent
from context.database import db
from sqlalchemy.orm.attributes import flag_modified


campaign_id = FunctionProperty(name="campaign_id", paramater_type="string", description="The ID of the outreach campaign this agent is texting for")
voter_id = FunctionProperty(name="voter_id", paramater_type="string", description="The ID of the voter this agent is texting")
inbound_message = FunctionProperty(name="inbound_message", paramater_type="string", description="The message received from the voter")


class GenerateResponse(AIFunction):

    def __init__(self, name="generate_response",description="generate a response with the agent previously created for this campaign and voter. Will send an notification back to the planner when the message is prepared.", parameters=[campaign_id, voter_id, inbound_message]):
        super().__init__(name, description, parameters)

    def call(self, **kwargs):
        print("Calling GenerateResponse")
        # check if the required arguments are included
        if "campaign_id" not in kwargs.keys():
            return "Missing required argument: campaign_id"
        if "voter_id" not in kwargs.keys():
            return "Missing required argument: voter_id"
        if "inbound_message" not in kwargs.keys():
            return "Missing required argument: inbound_message"
        
        # unpack paramaters to variables
        campaign_id = kwargs["campaign_id"]
        voter_id = kwargs["voter_id"]
        inbound_message = kwargs["inbound_message"]

        #get hydrated campaign object
        campaign = Campaign.query.filter_by(id=campaign_id).first()

        # get the texting agent for this campaign and voter
        relationship = SenderVoterRelationship.query.filter_by(voter_id=voter_id, sender_id=campaign.sender_id).first()

        print(f"Relationship agents available: {relationship.agents}")



        # get the interaction associated with this texting agent, campaign, and voter
        print(f"Looking for an interaction with campaign_id {campaign_id} and voter_id {voter_id}")
        interaction = Interaction.query.filter_by(campaign_id=campaign_id, voter_id=voter_id).first()
        
        # do a query for an agent with the interaction in it's interactions list
        texting_agent = TextingAgent.query.filter(TextingAgent.interactions.any(id=interaction.id)).first()

        # send the message to the texting agent
        last_message = texting_agent.send_prompt({
            "content": inbound_message,
        })["llm_response"]

        print(f"Texting agent generated a response {last_message}")
        
        if not interaction:
            return "No interaction found for this campaign and voter"

        interaction.conversation = texting_agent.conversation_history.copy()

        flag_modified(interaction, "conversation")

        # save the interaction and texting agent
        db.session.add(interaction)
        db.session.add(texting_agent)
        db.session.commit()
        db.session.close()

        print(f"Texting agent generated a response that is ready to be sent: {last_message}")

        return f"Texting agent generated a response. Call the function to send it. You do not need to create a new texting agent. Campaign ID {campaign_id}. Voter ID {voter_id}. The message is: {last_message}"
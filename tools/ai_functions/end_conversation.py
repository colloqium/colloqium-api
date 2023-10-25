from tools.ai_functions.ai_function import AIFunction, FunctionProperty
from context.database import db
from models.sender import Campaign
from models.interaction import SenderVoterRelationship, Interaction
from sqlalchemy.orm.attributes import flag_modified
from models.ai_agents.texting_agent import Agent

campaign_id = FunctionProperty(name="campaign_id", paramater_type="string", description="The ID of the outreach campaign this agent is texting for")
voter_id = FunctionProperty(name="voter_id", paramater_type="string", description="The ID of the voter this agent is texting")
inbound_message = FunctionProperty(name="inbound_message", paramater_type="string", description="The message the voter sent")
ending_reason = FunctionProperty(name="ending_reason", paramater_type="string", description="The reason the conversation is ending")

class EndConversation(AIFunction):

    def __init__(self, name="end_conversation",description="End the conversation with the votera and do not send a response. Can end either because the conversation has reached it's goal or if voter mentions violence or other inappropriate content. This should not be used if the voter is just disinterested.", parameters=[campaign_id, voter_id, ending_reason, inbound_message]):
        super().__init__(name, description, parameters)

    def call(self, **kwargs):
        print("Calling EndConversation")
        print(kwargs)
        
        # check if the required arguments are included
        if "campaign_id" not in kwargs.keys():
            return "Missing required argument: campaign_id"
        if "voter_id" not in kwargs.keys():
            return "Missing required argument: voter_id"
        if "inbound_message" not in kwargs.keys():
            return "Missing required argument: inbound_message"
        if "ending_reason" not in kwargs.keys():
            return "Missing required argument: ending_reason"
        
        # unpack paramaters to variables
        campaign_id = kwargs["campaign_id"]
        voter_id = kwargs["voter_id"]
        inbound_message = kwargs["inbound_message"]
        ending_reason = kwargs["ending_reason"]

        #get hydrated campaign object
        campaign = Campaign.query.filter_by(id=campaign_id).first()

        # get the texting agent for this campaign and voter
        relationship = SenderVoterRelationship.query.filter_by(voter_id=voter_id, sender_id=campaign.sender_id).first()

        print(f"Relationship agents available: {relationship.agents}")

        # get the planning agent for this sender voter Relationship. look for an agent with a name "planning_agent"
        planning_agent = [agent for agent in relationship.agents if agent.name == "planning_agent"][0]


        # get the interaction associated with this texting agent, campaign, and voter
        print(f"Looking for an interaction with campaign_id {campaign_id} and voter_id {voter_id}")
        interaction = Interaction.query.filter_by(campaign_id=campaign_id, voter_id=voter_id).first()
        
        # do a query for an agent with the interaction in it's interactions list and the name "texting_agent"
        texting_agent = Agent.query.filter(Agent.interactions.any(id=interaction.id), Agent.name == "texting_agent").first()

        texting_agent.conversation_history.append({
            "role": "assistant",
            "content": f"Conversation ended because {ending_reason}"
        })

        interaction.conversation = texting_agent.conversation_history.copy()

        flag_modified(interaction, "conversation")
        flag_modified(texting_agent, "conversation_history")

        # save the interaction and texting agent
        db.session.add(interaction)
        db.session.add(texting_agent)
        db.session.commit()
        ()

        planning_agent.send_message(f"Conversation with campaign_id {campaign_id} and voter_id {voter_id} ended because {ending_reason}")

        return "Conversation ended"
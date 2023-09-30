from models.ai_agents.agent import Agent
from models.interaction import SenderVoterRelationship
from context.database import db
from tools.ai_functions.function_list import ai_function_list
from tools.utility import get_llm_response_to_conversation, initialize_conversation
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate

class PlannerAgent(Agent):
    def __init__(self, sender_voter_relationship_id: int):
        
        sender_voter_relationship = SenderVoterRelationship.query.get(sender_voter_relationship_id)

        prompt_template = '''
            You are an agent for political campaign. Your job is to decide the best way to engage with voters to get them to vote for your candidate.

            You know the following about the candidate: {candidate_info}

            You know the following about the voter: {voter_info}

            Respond "Ready" if you are ready to begin and wait for a request from the campaign manager.
        '''

        system_prompt_template = SystemMessagePromptTemplate.from_template(prompt_template)

        chat_prompt_template = ChatPromptTemplate.from_messages([system_prompt_template])

        self.system_prompt = chat_prompt_template.format(
            candidate_info=sender_voter_relationship.sender.sender_information,
            voter_info=sender_voter_relationship.voter.voter_profile.to_dict()
        )

        super().__init__(self.system_prompt, "Planner Agent", "Handles scheduling and high-level decisions", sender_voter_relationship_id)

        self.conversation_history = initialize_conversation(self.system_prompt)

        first_llm_response = get_llm_response_to_conversation(self.conversation_history)

        self.conversation_history.append(first_llm_response)
        self.available_actions = [function for function in ai_function_list]

        db.session.add(self)
        db.session.commit()
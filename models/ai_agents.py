from models.base_db_model import BaseDbModel
from context.database import db
from tools.ai_functions.function_list import ai_function_list
from prompts.campaign_planner_agent import get_campaign_agent_system_prompt

class Agent(BaseDbModel):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    description = db.Column(db.String(200))
    sender_voter_relationship_id = db.Column(db.Integer, db.ForeignKey('sender_voter_relationship.id'))

    def __init__(self, system_prompt: str, name: str, description: str):
        self.system_prompt = system_prompt
        self.name = name
        self.description = description
        self.conversation_history = []
        self.available_actions = []


class PlannerAgent(Agent):
    def __init__(self):
        super().__init__(get_campaign_agent_system_prompt(), "Planner Agent", "Handles scheduling and high-level decisions")
        self.available_actions = [function.get_schema() for function in ai_function_list]


class TextingAgent(Agent):
    def __init__(self):
        super().__init__("Hi, I'm the texting agent", "Texting Agent", "Handles text message sending")

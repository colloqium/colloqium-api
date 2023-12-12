from sqlalchemy.exc import IntegrityError
from models.base_db_model import BaseDbModel
from tools.ai_functions.ai_function import AIFunction
from context.database import db
from tools.utility import get_llm_response_to_conversation
import json
from sqlalchemy import inspect
from sqlalchemy.orm.attributes import flag_modified


class Agent(BaseDbModel):
    __tablename__ = 'agent'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50)) # descriminator column
    description = db.Column(db.String(200))
    sender_voter_relationship_id = db.Column(db.Integer, db.ForeignKey('sender_voter_relationship.id'))
    interactions = db.relationship('Interaction', backref='agent', lazy=True)
    conversation_history = db.Column(db.JSON())
    available_actions = db.Column(db.JSON())

    __mapper_args__ = {
        'polymorphic_identity': 'agent',
        'polymorphic_on': name
    }

    def __init__(self, system_prompt: str, name: str, description: str, sender_voter_relationship_id: int):
        self.system_prompt = system_prompt
        self.name = name
        self.description = description
        self.sender_voter_relationship_id = sender_voter_relationship_id

        # check if self.available actions is a string or a list. If it is a string us json.loads to convert it to a list

        if isinstance(self.available_actions, str):
            self.available_actions = [AIFunction.from_dict(function_dict) for function_dict in json.loads(self.available_actions)] if self.available_actions else []
        elif isinstance(self.available_actions, list):
            self.available_actions = [AIFunction.from_dict(function_dict) for function_dict in self.available_actions] if self.available_actions else []
        else:
            self.available_actions = []
    @staticmethod
    def update_agent(agent):
        try:
            # Lock the row for the duration of this transaction
            agent_to_update = db.session.query(Agent).filter_by(id=agent.id).with_for_update().first()
            if agent_to_update is None:
                raise ValueError("Agent not found")
            
            db.session.commit()
            
            # Update the agent's attributes
            agent_to_update.conversation_history = agent.conversation_history.copy()

            # Commit the transaction to release the lock and save changes
            db.session.add(agent_to_update)
            db.session.commit()
            
        except IntegrityError as e:
            db.session.rollback()
            raise ValueError(f"Database update failed: {str(e)}")

    def last_message(self):
        """
        Returns the last message in the conversation history.
        
        Returns:
            last_message (dict): A dictionary containing the last message in the conversation history.
        """
        return self.conversation_history[-1]
    
    def to_dict(self):
        agent_dict = super().to_dict()
        agent_dict['conversation_history'] = self.conversation_history if self.conversation_history else []
        agent_dict['available_actions'] = [action.to_dict() for action in self.available_actions] if self.available_actions else []
        return agent_dict

    def send_prompt(self, prompt_data: dict):
        """
        Sends a prompt or instruction for the agent to carry out and updates the conversation.
        
        Parameters:
            prompt_data (dict): A dictionary containing all the necessary information for the prompt.
            
        Returns:
            result (dict): A dictionary containing the result of the operation.
        """

        with db.session.no_autoflush:

            db.session.flush()
            # Update conversation history with the new element
            print(f"{self.name} calling an agent with prompt data: {prompt_data}")
            self.conversation_history.append({
                "role": "user",
                "content": prompt_data['content']
            })

            flag_modified(self, "conversation_history")
            self.update_agent(self)

            self.available_actions = [AIFunction.from_dict(function_dict) for function_dict in json.loads(self.available_actions)] if self.available_actions else []

            # Convert available actions to a dictionary for faster lookup
            available_functions = {function.name: function for function in self.available_actions}
            function_schema_array = [function.get_schema() for function in self.available_actions]

            # Call the get_llm_response_to_conversation function
            
            try:
                llm_response = get_llm_response_to_conversation(self.conversation_history, function_schema_array)
            except Exception as e:
                return {'status': 'failure', 'message': f"{self.name} response failed: {str(e)}"}
            

            #the openai api returns an object with json, I want to return a dict
            if not isinstance(llm_response, dict):
                llm_response = json.loads(llm_response)

            # Update the conversation history with the LLM's response
            self.conversation_history.append(llm_response)

            print(f"{self.name} LLM response: {llm_response}")
            print(f"{self.name} Last message in conversation history: {self.last_message()}")

            #serialize available functions
            self.available_actions = json.dumps([function.to_dict() for function in self.available_actions])

            flag_modified(self, "conversation_history")
            self.update_agent(self)

            #reload the available actions
            if isinstance(self.available_actions, str):
                self.available_actions = [AIFunction.from_dict(function_dict) for function_dict in json.loads(self.available_actions)] if self.available_actions else []
            elif isinstance(self.available_actions, list):
                self.available_actions = [AIFunction.from_dict(function_dict) for function_dict in self.available_actions] if self.available_actions else []
            else:
                self.available_actions = []

            try:
                # Check for a function call in the LLM's response
                while 'function_call' in llm_response:
                    function_name = llm_response['function_call']['name']
                    function_args = json.loads(llm_response['function_call']['arguments'])
                    function_to_call = available_functions.get(function_name, None)

                    print(f"{self.name} Calling function: {function_name}")

                    #serialize available functions so that if any db functions are called in the function, they will not throw an error
                    self.available_actions = json.dumps([function.to_dict() for function in self.available_actions])

                    if function_to_call is None:
                        function_response = "This function doesn't exist"
                    else:
                        function_response = function_to_call.call(**function_args)
                        print(f"Function response: {function_response}")
                    
                    # Update the conversation history with the function's response
                    self.conversation_history.append({
                        "role": "function",
                        "name": function_name,
                        "content": function_response
                    })

                    # Call the LLM again to get a new response considering the function's output
                    llm_response = get_llm_response_to_conversation(self.conversation_history, function_schema_array)
                    print(f"{self.name} LLM response: {llm_response}")

                    self.conversation_history.append(llm_response)

                    flag_modified(self, "conversation_history")
                    self.update_agent(self)

                    if 'function_call' in llm_response:
                        print(f"{self.name} The LLM returned another function call. Continuing to process...")
                        self.available_actions = [AIFunction.from_dict(function_dict) for function_dict in json.loads(self.available_actions)]
            except Exception as e:
                print(f"{self.name} Error in while loop: {str(e)}")
            
            try:
                
                # reserialize the available actions
                try:
                    self.available_actions = json.dumps([function.to_dict() for function in self.available_actions])
                except Exception as e:
                    print(f"{self.name} objects did not need to be deserialized: {str(e)}")

                db.session.flush()

                flag_modified(self, "conversation_history")
                self.update_agent(self)

            except Exception as e:
                # Handle database update errors
                print(f"{self.name} Database update failed: {str(e)}")
                return {'status': 'failure', 'message': f"Database update failed: {str(e)}"}

            print(f"{self.name} before return last message is: {self.last_message()}")
            # Return the LLM's last response
            return {
                'status': 'success',
                'message': "Prompt processed and conversation updated.",
                'llm_response': self.last_message()
            }
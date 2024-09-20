from sqlalchemy.exc import IntegrityError
from models.base_db_model import BaseDbModel
from tools.ai_functions.ai_function import AIFunction
from context.database import db
from tools.utility import get_llm_response_to_conversation
import json
from sqlalchemy.orm.attributes import flag_modified
from typing import Any


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
    
    def last_message_as_json(self) -> Any:
        '''
            Returns the last message in the conversation history as a json object.
        '''

        # check if the last message is json
        last_message = self.last_message()
        json_last_message = None

        try:
            json_last_message = json.loads(last_message['content'])
        except json.decoder.JSONDecodeError as error:
            print(f"Error decoding JSON from LLM response: {error}")
        
        return json_last_message

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
                "content": [{"type": "text", "text": prompt_data['content']}]
            })

            flag_modified(self, "conversation_history")
            self.update_agent(self)

            print(f"{self.name} available actions is: {self.available_actions}")
            if isinstance(self.available_actions, str):
                print(f"{self.name} available actions is a string")
                function_dicts = json.loads(self.available_actions)
                print(f"{self.name} function_dicts is: {function_dicts}")
                self.available_actions = [AIFunction.from_dict(function_dict) for function_dict in function_dicts] if function_dicts else []
            elif isinstance(self.available_actions, list):
                print(f"{self.name} available actions is a list")
                self.available_actions = [AIFunction.from_dict(function_dict) for function_dict in self.available_actions] if self.available_actions else []
            else:
                print(f"{self.name} available actions is not a string or list")
                self.available_actions = []

            print("Updated available actions")
            # Convert available actions to a dictionary for faster lookup
            available_functions = {function.name: function for function in self.available_actions}
            print(f"{self.name} available functions is: {available_functions}")
            function_schema_array = [function.get_schema() for function in self.available_actions]
            print(f"{self.name} function_schema_array is: {function_schema_array}")
           
            # Call the get_llm_response_to_conversation function
            
            try:
                print(f"{self.name} calling get_llm_response_to_conversation")
                llm_response = get_llm_response_to_conversation(self.conversation_history, function_schema_array)
            except Exception as e:
                return {'status': 'failure', 'message': f"{self.name} response failed: {str(e)}"}
            

            #the openai api returns an object with json, I want to return a dict
            if not isinstance(llm_response, dict):
                print(f"{self.name} llm_response is not a dict")
                llm_response = json.loads(llm_response)
            
            print(f"{self.name} llm_response is now a dict")
            # Update the conversation history with the LLM's response
            self.conversation_history.append({
                "role": "assistant",
                "content": llm_response['content']
            })

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
                while any(block['type'] == 'tool_use' for block in llm_response['content']):
                    for block in llm_response['content']:
                        if block['type'] == 'tool_use':
                            function_name = block['name']
                            function_args = block['input']
                            function_to_call = available_functions.get(function_name)
                            if function_to_call:
                                function_response = function_to_call.call(**function_args)
                            else:
                                function_response = "This function doesn't exist"

                            # Append the function result as a `tool_result` content block
                            self.conversation_history.append({
                                "role": "user",
                                "content": [{
                                    "type": "tool_result",
                                    "tool_use_id": block['id'],
                                    "content": function_response
                                }]
                            })
                            flag_modified(self, "conversation_history")
                            self.update_agent(self)

                            # Call the LLM again with the updated conversation
                            llm_response = get_llm_response_to_conversation(self.conversation_history, function_schema_array)
                            self.conversation_history.append({
                                "role": "assistant",
                                "content": llm_response['content']
                            })
                            flag_modified(self, "conversation_history")
                            self.update_agent(self)

                            print(f"{self.name} LLM response: {llm_response}")

                            if 'function_call' in llm_response:
                                print(f"{self.name} The LLM returned another function call. Continuing to process...")
                                
                                if isinstance(self.available_actions, str):
                                    self.available_actions = [AIFunction.from_dict(function_dict) for function_dict in json.loads(self.available_actions)] if self.available_actions else []
                                elif isinstance(self.available_actions, list):
                                    self.available_actions = [AIFunction.from_dict(function_dict) for function_dict in self.available_actions] if self.available_actions else []
                                else:
                                    self.available_actions = []
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
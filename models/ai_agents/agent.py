from models.base_db_model import BaseDbModel
from context.database import db
from tools.utility import get_llm_response_to_conversation
import json

class Agent(BaseDbModel):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    description = db.Column(db.String(200))
    sender_voter_relationship_id = db.Column(db.Integer, db.ForeignKey('sender_voter_relationship.id'))
    interactions = db.relationship('Interaction', backref='agent', lazy=True)
    conversation_history = db.Column(db.JSON())
    available_actions = db.Column(db.JSON())

    def __init__(self, system_prompt: str, name: str, description: str, sender_voter_relationship_id: int):
        self.system_prompt = system_prompt
        self.name = name
        self.description = description
        self.sender_voter_relationship_id = sender_voter_relationship_id
        self.conversation_history = []
        self.available_actions = []

    def last_message(self):
        """
        Returns the last message in the conversation history.
        
        Returns:
            last_message (dict): A dictionary containing the last message in the conversation history.
        """
        return self.conversation_history[-1]

    def send_prompt(self, prompt_data: dict):
      """
      Sends a prompt or instruction for the agent to carry out and updates the conversation.
      
      Parameters:
          prompt_data (dict): A dictionary containing all the necessary information for the prompt.
          
      Returns:
          result (dict): A dictionary containing the result of the operation.
      """

      # Update conversation history with the new element
      self.conversation_history.append({
          "role": "user",
          "content": prompt_data['content']
      })

      # Convert available actions to a dictionary for faster lookup
      available_functions = {function.name: function for function in self.available_actions}
      function_schema_array = [function.get_schema() for function in self.available_actions]

      # Call the get_llm_response_to_conversation function
      llm_response = get_llm_response_to_conversation(self.conversation_history, function_schema_array)

      # Update the conversation history with the LLM's response
      self.conversation_history.append(llm_response)

      # Check for a function call in the LLM's response
      while 'function_call' in llm_response:
          function_name = llm_response['function_call']['name']
          function_args = json.loads(llm_response['function_call']['arguments'])
          function_to_call = available_functions.get(function_name, None)

          if function_to_call is None:
              function_response = "This function doesn't exist"
          else:
              function_response = function_to_call.call(**function_args)
          
          # Update the conversation history with the function's response
          self.conversation_history.append({
              "role": "function",
              "name": function_name,
              "content": function_response
          })

          # Call the LLM again to get a new response considering the function's output
          llm_response = get_llm_response_to_conversation(self.conversation_history, function_schema_array)
          self.conversation_history.append(llm_response)

      try:
          # Update the database with the updated conversation_history
          db.session.add(self)
          db.session.commit()
      except Exception as e:
          # Handle database update errors
          return {'status': 'failure', 'message': f"Database update failed: {str(e)}"}

      # Return the LLM's last response
      return {
          'status': 'success',
          'message': "Prompt processed and conversation updated.",
          'llm_response': llm_response['content']
      }
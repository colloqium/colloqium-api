from typing import List
from dataclasses import dataclass
import json
@dataclass
class FunctionProperty:
    name: str # name of the property
    paramater_type: str # type of the property
    description: str # description of the property so the agent can know what it does and how to use it

    def to_dict(self):
        return {
            'class_name': self.__class__.__name__,
            'name': self.name,
            'paramater_type': self.paramater_type,
            'description': self.description
        }
    
    @classmethod
    def from_dict(cls, property_dict):
        print(f"Calling from_dict with property_dict: {property_dict}")
        return cls(
            name=property_dict['name'],
            paramater_type=property_dict['paramater_type'],
            description=property_dict['description']
        )


@dataclass
class AIFunction():

    name: str # name of the function
    description: str # description of the function so the agent can know what it does and decide whether to use it
    parameters: List[FunctionProperty] # parameters of the function so the agent can know what it needs to run the function
    schema: str # schema of the function so the agent can know what it needs to run the function includes name description and paramaters
    _registry = {}  # Class variable to hold the registry
    
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        AIFunction._registry[cls.__name__] = cls 

    def __init__(self, name, description, parameters):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.schema = self.get_schema()
    
    def call(self, **kwargs):
        raise NotImplementedError("This function has not been implemented yet")
    
    # make this class serializable
    def to_dict(self):
        
        parameters = [param.to_dict() for param in self.parameters]
        # return the schema as a dictionary object
        return {
            'class_name': self.__class__.__name__, # this is the name of the class so we can find it in the registry
            'name': self.name,
            'description': self.description,
            'parameters': parameters
        }
    
    @classmethod
    def from_dict(cls, function_dict):
        print(f"Calling from_dict with function_dict: {function_dict}")
        class_name = function_dict.pop('class_name', None)
        if class_name and class_name in cls._registry:
            print(f"Class in registry: {class_name}")
            return cls._registry[class_name].from_dict(function_dict)
        else:
            name = function_dict['name']
            print(f"Class not in registry: {name}")
            description = function_dict['description']
            print(f"Description: {description}")
            
            # Get parameters data
            parameters_data = function_dict['parameters']
            param_type = type(parameters_data)
            print(f"Type of parameters_data: {param_type}")
            print(f"Value of parameters_data: {parameters_data}")
            
            # Build the list of FunctionProperty instances
            parameters = []
            if param_type == list:
                for param_info in parameters_data:
                    print(f"Processing parameter as a list: {param_info}")
                    parameters.append(
                        FunctionProperty(
                            name=param_info['name'],
                        paramater_type=param_info['paramater_type'],
                        description=param_info['description']
                        )
                    )
            elif param_type == dict:
                print(f"Processing parameter as a dict: {parameters_data}")
                properties = parameters_data['properties']
                for name, prop_details in properties.items():
                    parameters.append(
                        FunctionProperty(
                        name=name,
                        paramater_type=prop_details['type'],
                        description=prop_details['description']
                        )
                    )
            else:
                print(f"Unexpected type for parameters: {param_type}")
            
            print(f"Parameters: {parameters}")
            return cls(name, description, parameters)

    
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
                "properties": {parameter.name: {"type": parameter.paramater_type, "description": parameter.description} for parameter in self.parameters},
                "required": [parameter.name for parameter in self.parameters]
            }
        }
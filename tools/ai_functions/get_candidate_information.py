from tools.ai_functions.ai_function import AIFunction, FunctionProperty
from tools.vector_store_utility import get_vector_store_results
from dataclasses import dataclass
import json

inbound_message = FunctionProperty(name="inbound_message", paramater_type="string", description="The message the voter sent")
query = FunctionProperty(name="query", paramater_type="string", description="The query that you want to search for. Should include a question about a specific policy or background information about the candidate")
sender_id = FunctionProperty(name="sender_id", paramater_type="string", description="The ID of the sender this agent is texting for")

@dataclass
class GetCandidateInformation(AIFunction):

    def __init__(self, name="get_candidate_information",description="Get information about a candidates positions or background that you don't already have", parameters=[inbound_message, query, sender_id]):
        super().__init__(name,description,parameters)

    def call(self, **kwargs):
        print("Calling GetCandidateInformation")

        # check if the arguments include inbound_message
        if "inbound_message" not in kwargs.keys():
            return "Missing required argument: inbound_message"
        
        # check if the arguments include query
        if "query" not in kwargs.keys():
            return "Missing required argument: query"
        
        # check if the arguments include sender_id
        if "sender_id" not in kwargs.keys():
            return "Missing required argument: sender_id"
        
        # unpack paramaters to variables
        inbound_message = kwargs["inbound_message"]
        query = kwargs["query"]
        sender_id = kwargs["sender_id"]

        vector_meta = {
            'context': 'sender',
            'id': sender_id
        }

        #TODO add a step where another agent tries to summarize the question to get better results

        results = get_vector_store_results(query,1, 0.75, vector_meta)

        # get the results["text"] from each example and remove the brackets
        results = [example["text"] for example in results]

        # remove all [ and { }] from the examples
        results = [example.replace("[", "").replace("]", "").replace("{", "").replace("}", "") for example in results]


        return f"You have the following related context about the sender. Decide which parts are relevant for your response to the voter and incorporate them. Remember, you're sending a text message. {json.dumps(results)}"
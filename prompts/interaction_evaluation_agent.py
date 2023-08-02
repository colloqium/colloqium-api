from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate
from models.models import Interaction

def get_conversation_evaluation_system_prompt(conversation: [{}]):

    # GPT API System Prompts
    system_prompt = ''' 
                You are about to evaluate a conversation where the assistant's goal was defined by the initial system prompt. Please consider the assistant's effectiveness in achieving this goal based on the conversation that followed. Identify any new information about the recipient that was not known at the beginning of the conversation. Return your evaluation as a json object in the following format:
                
                {{
                    "insights_about_recipient": new information about the recipient,
                    "insights_about_issues": What policiy issue areas were discussed in this conversation? What was the sentiment of the recipient on these issues? Assume this will later be aggregated across many conversations.,
                    "campaign_insights": What information from this would be helpful for the sender to know? What might this suggest for follow up questions or trends in voter sentiment? Assume this will later be aggregated across many conversations.,
                    "campaign_goal": what was the objective of this conversation
                    "goal_achieved": "True or False depending on if the goal was achived",
                    "rating_explanation": explanation for why the agent deserves the rating taking in to account the goal, new information recieved, and their overall effectiveness
                    "rating": rating from 1 to 10,
                    "campaign_relevance_explanation": explanation for why this conversation is relevant to the campaign staff. For example, this is informatino that is not brought up anywhere else or the recipient is a key influencer in the community,
                    "campaign_relevance_score": score from 1 to 100 for how relevant this conversation is to the campaign staff. Will be used to decide which messages to highlight to the campaign,
                    "campaign_relevance_summary": summary of why this conversation is relevant to the campaign staff. Will be used to aggregate relevant information across many conversations,
                }}

                The conversation to evaluate is:
                {conversation}'''


    system_message_prompt = SystemMessagePromptTemplate.from_template(
        system_prompt)

    chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt])

    output = chat_prompt.format(conversation=conversation)

    return output
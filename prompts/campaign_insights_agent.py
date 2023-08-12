from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate
from models.sender import Campaign, Sender


def get_campaign_summary_system_prompt(campaign: Campaign):

    # Get an array of all the summary information from each interaction in this campaign
    # relevant fields are: goal_achieved, rating_explanation, rating, campaign_relevance_score, campaign_relevance_explanation, campaign_relevance_summary, insights_about_issues, insights_about_voter
    interactions = campaign.interactions
    sender = Sender.query.get(campaign.sender_id)

    # Get the relevant fields for all interactions and append them to an array
    interaction_summaries = ""

    for interaction in interactions:
        interaction_string = "Interaction for voter {interaction.voter.voter_name} - "
        interaction_string += f"Goal achieved: {interaction.goal_achieved} "
        interaction_string += f"Rating explanation: {interaction.rating_explanation} "
        interaction_string += f"Rating: {interaction.rating} "
        interaction_string += f"Campaign relevance score: {interaction.campaign_relevance_score} "
        interaction_string += f"Campaign relevance explanation: {interaction.campaign_relevance_explanation} "
        interaction_string += f"Campaign relevance summary: {interaction.campaign_relevance_summary} "
        interaction_string += f"Insights about issues: {interaction.insights_about_issues} "
        interaction_string += f"Insights about voter: {interaction.insights_about_voter} "
        interaction_string += "\n"
        interaction_summaries += interaction_string


    print (f"Interaction summary: {interaction_summaries}")

    
        

    # GPT API System Prompts
    system_prompt = ''' 
                You are a senior campaign manager with experience in field organizing, communications, fundraising and everything else a campaign might need.

                Your team has just finished a specific outreach effort to voters in a specific area. You are reviewing the results of the outreach effort and preparing a summary of the results for the campaign manager.

                You will generate:
                1. An overview of policy insights from the campaign by category
                1. A summary of key insights and takeaways for the communications director
                2. A summary of key insights and takeaways for the field director
                3. A summary of the key insights and takeaways for the campaign manager

                You should be concise, and make sure the information is actionable for the campaign team. It is better to say less and be clear than to say more and be confusing.

                Your output should be a json object in the following format:

                {{
                    "policy_insights": {{ "policy_category_1": "policy_insight", "policy_category_2": "policy_insight" }},
                    "communications_director_summary": "summary of key insights and takeaways for the communications director",
                    "field_director_summary": "summary of key insights and takeaways for the field director",
                    "campaign_manager_summary": "summary of key insights and takeaways for the campaign manager taking in to account the hihglights from the policy insights, communications director summary, and field director summary"
                }}

                You know the following about the campaign:
                {sender_information}

                Here are the conversations summaries that you should use to generate the insights:
                {interaction_summaries}         
                '''
 

    system_message_prompt = SystemMessagePromptTemplate.from_template(
        system_prompt)

    chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt])

    output = chat_prompt.format(sender_information=sender.sender_information, interaction_summaries=interaction_summaries)

    print(f"Campaign Summary System prompt: {output}")

    return output
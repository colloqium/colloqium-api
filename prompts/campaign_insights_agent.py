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
        interaction_string = f"Interaction for voter {interaction.voter.voter_name} - "
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
                You are a senior campaign manager experienced in all facets of campaign operations.

                Your team has recently wrapped up a targeted voter outreach in a specific locale. Your task is to distill the outreach results into razor-sharp summaries for the campaign team.

                Your output will be:
                1. Categorized policy takeaways.
                2. A sub-20 word summary for the Communications Director.
                3. A sub-20 word summary for the Field Director.
                4. A sub-20 word summary for the Campaign Manager, considering all the above.

                Aim for brevity and clarity in your summaries, ensuring they are actionable. Less is more.

                Output your findings in the following JSON format:

                {{
                    "policy_insights": {{ "category_1": "insight", "category_2": "insight" }},
                    "communications_director_summary": "concise insights for comms",
                    "field_director_summary": "concise insights for field",
                    "campaign_manager_summary": "concise, holistic insights"
                }}

                Campaign Context:
                {sender_information}

                Interaction Data:
                {interaction_summaries}

                '''
 

    system_message_prompt = SystemMessagePromptTemplate.from_template(
        system_prompt)

    chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt])

    output = chat_prompt.format(sender_information=sender.example_interactions, interaction_summaries=interaction_summaries)

    print(f"Campaign Summary System prompt: {output}")

    return output
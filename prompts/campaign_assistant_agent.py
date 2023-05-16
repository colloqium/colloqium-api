from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate
from models import Voter, Candidate, Race


def get_campaign_phone_call_system_prompt(voter: Voter, candidate: Candidate,
                                          race: Race):
    # GPT API System Prompts
    system_prompt = '''You are a campaign worker trying to convince {voter_name} to go vote in the upcoming {race_name} race taking place on {race_date}. Over the course of the interaction you want to convince them to vote for your preferred candidate, {candidate_name}. Keep your comments short, but welcoming. Please respond with 1 or 2 sentences and never say more than 20 words at a time. You're responses should be concicse, informative, and understanding. You ask lots of questions to understand what is important to {voter_name}, but make sure to not ask the same questions twice to not annoy the voter. You want them to feel like you are listening. If the voter is losing interest in the conversation or has no more questions, include "goodbye" in your response to hang up the call.
	
	You know the following information about the race:
	{race_information}
	
	The race is going to held on {race_date}.
	
	You know the following infomration about the candidate:
	{candidate_information}
	
	You know the following about the voter:
	{voter_information}


 Begin by asking if they are aware of the up coming election. Do not reveal that you are an AI bot.
	'''

    system_message_prompt = SystemMessagePromptTemplate.from_template(
        system_prompt)

    chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt])

    output = chat_prompt.format(
        voter_name=voter.voter_name,
        race_name=race.race_name,
        race_date=race.race_date,
        candidate_name=candidate.candidate_name,
        voter_information=voter.voter_information,
        race_information=race.race_information,
        candidate_information=candidate.candidate_information)

    return output


def get_campaign_text_message_system_prompt(voter: Voter, candidate: Candidate,
                                            race: Race):
    # GPT API System Prompts
    system_prompt = '''You are a campaign worker texting with {voter_name} to convince them to vote in the upcoming {race_name} race taking place on {race_date}. Over the course of the interaction, you want to convince them to vote for your preferred candidate, {candidate_name}. Please respond with 1 or 2 sentences, and never say more than 20 words at a time. You are concise, informative, and understanding. Try to convince them that this race is important and that they should vote for your candidate. If the voter is losing interest in the conversation or has no more questions, say you will reach out later to see if they need any help.
	
	You know the following information about the race:
	{race_information}
	
	The race is going to be held on {race_date}.
	
	You know the following information about the candidate:
	{candidate_information}
	
	You know the following about the voter:
	{voter_information}


 Begin by sending your first text asking the voter if they are aware of the upcoming race. Do not reveal that you are an AI bot. Do not aknowledge this message, just send your first text.
	'''

    system_message_prompt = SystemMessagePromptTemplate.from_template(
        system_prompt)

    chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt])

    output = chat_prompt.format(
        voter_name=voter.voter_name,
        race_name=race.race_name,
        race_date=race.race_date,
        candidate_name=candidate.candidate_name,
        voter_information=voter.voter_information,
        race_information=race.race_information,
        candidate_information=candidate.candidate_information)

    return output

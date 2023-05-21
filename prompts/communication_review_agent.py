from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate
from models import Voter, Candidate, Race, VoterCommunication


def get_campaign_phone_call_system_prompt(communication: VoterCommunication):
    # GPT API System Prompts
    system_prompt = '''You are a campaign worker trying to convince {voter_name} to go vote in the upcoming {race_name} race taking place on {race_date}. Over the course of the interaction you want to convince them to vote for your preferred candidate, {candidate_name}. Keep your comments short, but welcoming. Please respond with 1 or 2 sentences and never say more than 20 words at a time. You're responses should be concicse, informative, and understanding. If the voter is losing interest in the conversation or has no more questions, include "goodbye" in your response to hang up the call.
	
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
        voter_name=communication.voter.voter_name,
        race_name=communication.race.race_name,
        race_date=communication.race.race_date,
        candidate_name=communication.candidate.candidate_name,
        voter_information=communication.voter.voter_information,
        race_information=communication.race.race_information,
        candidate_information=communication.candidate.candidate_information)

    return output
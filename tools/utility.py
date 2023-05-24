from models import VoterCommunication
from logs.logger import logging
import openai
from database import db
import re
import time

def add_message_to_conversation(voter_communication: VoterCommunication, message) -> []:
    """
    This function should append the new message to the voter_communication conversation.
    """
    logging.info(f"Updating conversation with new message: {message}")
    conversation = voter_communication.conversation.copy()
    conversation.append({"role": "user", "content": message})
    return conversation

def add_llm_response_to_conversation(voter_communication: VoterCommunication) -> str:
    conversation = voter_communication.conversation.copy()
    response_content = ""
    retry_count = 0
    max_retries = 5  # maximum number of retries
    wait_time = 2  # wait time in seconds
    
    while retry_count < max_retries:
        try:
            # generate a new response from OpenAI to continue the conversation
            logging.info("Starting OpenAI Completion")
            completion = openai.ChatCompletion.create(model="gpt-4",
                                                    messages=conversation,
                                                    temperature=0.9)
            logging.info("Finished OpenAI Completion")
            response_content = completion.choices[0].message.content
            conversation.append({"role": "assistant", "content": response_content})
            logging.info(f"Adding OpenAI response to conversation: {response_content}")

            voter_communication.conversation = conversation
            db.session.add(voter_communication)
            db.session.commit()
            break
        except openai.error.RateLimitError:
            # sleep for a while before retrying
            logging.info(f"Model overloaded, waiting for {wait_time} seconds before retry...")
            time.sleep(wait_time)
            retry_count += 1
            continue
    
    if retry_count == max_retries:
        logging.error("Max retries reached, OpenAI model still overloaded.")
    
    return response_content

def initialize_conversation(system_prompt: str) -> [{}]:
    return [{"role": "system", "content": system_prompt}]

def remove_trailing_commas(json_like):
    json_like = re.sub(",[ \t\r\n]+}", "}", json_like)
    json_like = re.sub(",[ \t\r\n]+\]", "]", json_like)
    return json_like
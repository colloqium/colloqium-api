# from logs.logger import logger
import random
import openai
import re
import time

def add_message_to_conversation(conversation: [{}],message: {}) -> []:
    """
    This function should append the new message to the recipient_communication conversation.
    """
    (f"Updating conversation with new message: {message}")
    conversation = conversation.copy()
    conversation.append({"role": "user", "content": message})
    return conversation


def get_llm_response_to_conversation(conversation: [{}]) -> {}:
    conversation = conversation.copy()
    response_content = ""

    # have a random wait time between 20 and 30 seconds to avoid hitting the rate limit
    wait_time =  50 + 10 * random.random()

    while response_content == "":
        try:
            # generate a new response from OpenAI to continue the conversation
            ("Starting OpenAI Completion")
            completion = openai.ChatCompletion.create(model="gpt-4",
                                                      messages=conversation,
                                                      temperature=0.9)
            ("Finished OpenAI Completion")
            response_content = completion.choices[0].message.content
            conversation.append({
                "role": "assistant",
                "content": response_content
            })
            # print(f"Adding OpenAI response to conversation: {response_content}")
            conversation = conversation
            break
        except openai.error.RateLimitError:
            # sleep for a while before retrying
            print(f"Model hit rate limit, waiting for {wait_time} seconds before retry...")
            time.sleep(wait_time)
            retry_count += 1
            continue
        except openai.error.ServiceUnavailableError:
            print(f"Model overloaded, waiting for {wait_time} seconds before retry...")
            time.sleep(wait_time)
            retry_count += 1
            continue

    return conversation[-1]


def initialize_conversation(system_prompt: str) -> [{}]:
    return [{"role": "system", "content": system_prompt}]


def remove_trailing_commas(json_like):
    json_like = re.sub(",[ \t\r\n]+}", "}", json_like)
    json_like = re.sub(",[ \t\r\n]+\]", "]", json_like)
    return json_like

def format_phone_number(phone_number: str) -> str:
    """
    This function should format the phone number to be in the format +1xxxxxxxxxx

    It should check whether or not the number has the +1 country code, if not, it should add it.
    """
    digits = [char for char in phone_number if char.isdigit()]
    if len(digits) == 10:
        return "+1" + "".join(digits)
    elif len(digits) == 11:
        return "+" + "".join(digits[0:])
    else:
        return phone_number
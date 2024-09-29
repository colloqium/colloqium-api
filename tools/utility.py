# from logs.logger import logger
import random
import re
import time
from typing import List, Dict
import os
import requests

def add_message_to_conversation(conversation: List[Dict[str, str]], message: Dict[str, str]) -> List[Dict[str, str]]:
    """
    This function should append the new message to the recipient_communication conversation.
    """
    (f"Updating conversation with new message: {message}")
    conversation = conversation.copy()
    conversation.append({"role": "user", "content": message})
    return conversation


def get_llm_response_to_conversation(conversation, functions=[]):
    conversation = conversation.copy()
    response_content = ""

    max_retries = 20
    retry_count = 0

    while retry_count < max_retries:
        try:
            headers = {
                "Content-Type": "application/json",
                "api-key": os.getenv("AZURE_OPENAI_API_KEY"),
            }
            endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
            payload = {
                "messages": conversation,
                "temperature": 0.9,
            }

            if not functions == []:
                payload["functions"] = functions
                payload["function_call"] = "auto"

            # Generate a new response from OpenAI to continue the conversation
            print(f"payload: {payload}")
            response = requests.post(endpoint, headers=headers, json=payload)
            response.raise_for_status()

            response_content = response.json()["choices"][0]["message"]
            conversation.append(response_content)
            break  # Exit the loop if the request is successful

        except requests.exceptions.HTTPError as http_err:
            error_status = response.status_code
            error_message = response.json().get("error", {}).get("message", "")
            print(f"HTTP Error {error_status}: {error_message}")

            if error_status == 429:
                # Rate limit exceeded
                wait_time = random.randint(60, 90)
                print(f"Rate limit exceeded. Retrying in {wait_time} seconds...")
            else:
                # Other HTTP errors
                wait_time = 5  # Shorter wait time for other errors
                print(f"Retrying in {wait_time} seconds...")

            retry_count += 1
            time.sleep(wait_time)
            continue

        except Exception as e:
            print(f"Unexpected error: {e}")
            wait_time = 5  # Short wait time for unexpected errors
            print(f"Retrying in {wait_time} seconds...")
            retry_count += 1
            time.sleep(wait_time)
            continue

    if retry_count == max_retries:
        raise Exception("Maximum retries exceeded")

    return conversation[-1]


def initialize_conversation(system_prompt: str) -> List[Dict[str, str]]:
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
# from logs.logger import logger
import random
import anthropic
import re
import time
from typing import List, Dict
import anthropic
import json
from tools.ai_functions.ai_function import AIFunction

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
    retry_count = 0
    max_retries = 1

    # Prepare the messages and tools for Anthropic's API
    formated_messages = format_messages_for_anthropic(conversation)
    print(f"formated_messages is: {formated_messages}")
    tools = functions  # Anthropic uses 'tools' instead of 'functions'

    # Build the API request payload
    request_payload = {
        "model": "claude-3-sonnet-20240229",  # Update to the desired Claude model
        "messages": formated_messages,
        "max_tokens": 1000,
        "temperature": 0.9,
    }
    if tools:
        print(f"tools is: {tools}")
        #replace tools.0.paramaters with tools.0.input_schema
        for tool in tools:
            tool["input_schema"] = tool["parameters"]
            del tool["parameters"]
        request_payload["tools"] = tools

    while retry_count <= max_retries:
        try:
            # Send the request to Anthropic's API
            anthropic_client = anthropic.Anthropic()
            print(f"request_payload is: {request_payload}")
            completion = anthropic_client.messages.create(**request_payload)
            print(f"completion is: {completion}")
            response_content = completion["content"]

            # Process the response (parse content blocks)
            llm_response = json.loads(response_content)
            conversation.append(llm_response)
            break
        except Exception as e:
            print(f"Error: {e}")
            retry_count += 1
            if retry_count > max_retries:
                raise e

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

def format_messages_for_anthropic(messages):
    
    print("Formatting messages for Anthropic")
    formatted_messages = []
    current_role = None
    current_content = []

    for message in messages:
        print(f"message is: {message}")
        role = message['role']
        content = message.get('content', '')

        if role == 'system' or role == 'function':
            role = 'user'

        if role != current_role:
            if current_role:
                formatted_messages.append({
                    'role': current_role,
                    'content': '\n'.join(current_content)
                })
            current_role = role
            current_content = [content]
        else:
            current_content.append(content)
        print(f"current_content is: {current_content}")


    if current_role:
        print(f"current_role is: {current_role}")
        formatted_messages.append({
            'role': current_role,
            'content': '\n'.join(current_content)
        })

    print(f"formatted_messages is: {formatted_messages}")

    return formatted_messages

if __name__ == "__main__":
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "system", "content": "Glycolysis is the process of breaking down glucose into pyruvate."},
        {"role": "user", "content": "What is the capital of France?"},
        {"role": "assistant", "content": "The capital of France is Paris."},
        {"role": "assistant", "content": "The capital of Germany is Berlin."},
        {"role": "function", "content": "Glycolysis is the process of breaking down glucose into pyruvate."},
        {"role": "user", "content": "What is the capital of Germany?"},
    ]
    print(format_messages_for_anthropic(messages))
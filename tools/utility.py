# from logs.logger import logger
import random
import openai
import re
import time
from typing import List, Dict
from langchain.text_splitter import CharacterTextSplitter
from context.vector_store import get_index_from_context, save_vector_plus_meta, get_top_relevant_messages

from typing import List, Dict

def add_message_to_conversation(conversation: List[Dict[str, str]], message: Dict[str, str]) -> List[Dict[str, str]]:
    """
    This function should append the new message to the recipient_communication conversation.
    """
    (f"Updating conversation with new message: {message}")
    conversation = conversation.copy()
    conversation.append({"role": "user", "content": message})
    return conversation


def add_to_vector_store(content: str, metadata: dict) -> None:
    """
    This function should add the content and metadata to the vector store.
    """

    # chunck the content into 1024 token size chuncks that overlap by 512 tokens
    text_splitter  = CharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=500,
        chunk_overlap=100,
        separator = " ",
    )

    chuncks = text_splitter.split_text(content)

    print(f"*************************Chuncks**********************************\n{chuncks}")

    index = get_index_from_context(metadata['context'])
    
    # for each chunck save the vector and metadata to the vector store
    for chunck in chuncks:
        #check if the chunk is already in the vector store
        # if it is, skip it
        current_results = get_top_relevant_messages(chunck, index, top_k=1, similarity_threshold=0.9999, metadata=metadata)

        if len(current_results) != 0:
            continue

        save_vector_plus_meta(chunck, metadata, index)


def get_vector_store_results(query: str, metadata: dict, top_k=3, similarity=0.5) -> List[Dict[str, str]]:

    # get the right vector store from pinecone for the metadata. Sender, Voter, or General information
    index = get_index_from_context(metadata['context'])

    return get_top_relevant_messages(query, index, top_k, similarity, metadata)


def get_llm_response_to_conversation(conversation, functions = []):
    conversation = conversation.copy()
    response_content = ""


    # have a random wait time between 30 and 60 seconds to avoid hitting the rate limit
    wait_time =  random.randint(30, 60)

    max_retries = 50
    retry_count = 0

    while retry_count <= max_retries:
        try:
            # generate a new response from OpenAI to continue the conversation

            if functions == []:
                completion = openai.ChatCompletion.create(model="gpt-4",
                                                      messages=conversation,
                                                      temperature=0.9)
            else:
                completion = openai.ChatCompletion.create(model="gpt-4-0613",
                                                      messages=conversation,
                                                      functions=functions,
                                                      function_call="auto",
                                                      temperature=0.9)

            '''
            Response in the following formats:

                    {
                        "id": "chatcmpl-123",
                        ...
                        "choices": [{
                            "index": 0,
                            "message": {
                            "role": "assistant",
                            "content": null,
                            "function_call": {
                                "name": "get_current_weather",
                                "arguments": "{ \"location\": \"Boston, MA\"}"
                            }
                            },
                            "finish_reason": "function_call"
                        }]
                    }

                    or

                    {
                        "id": "chatcmpl-123",
                        ...
                        "choices": [{
                            "index": 0,
                            "message": {
                            "role": "assistant",
                            "content": "The weather in Boston is currently sunny with a temperature of 22 degrees Celsius.",
                            },
                            "finish_reason": "stop"
                        }]
                    }
            '''
            response_content = completion.choices[0].message


            conversation.append(response_content)
            # print(f"Adding OpenAI response to conversation: {response_content}")
            conversation = conversation
            break
        except openai.error.RateLimitError:
            wait_time = random.randint(30, 60)
            # sleep for a while before retrying
            print(f"Model hit rate limit, waiting for {wait_time} seconds before retry...")
            time.sleep(wait_time)
            retry_count += 1
            continue
        except openai.error.ServiceUnavailableError:
            wait_time = random.randint(30, 60)
            print(f"Model unavailable, waiting for {wait_time} seconds before retry...")
            time.sleep(wait_time)
            retry_count += 1
            continue

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
import os
import tiktoken
import pinecone


tokenizer = tiktoken.get_encoding('gpt2')

EMBEDDINGS_MODEL = "text-embedding-ada-002"
INDEX_DIMENSIONS = 1536 # specific for "text-embedding-ada-002" model

pinecone.init(
    api_key = os.getenv('PINECONE_API_KEY'),
    environment = os.getenv('PINECONE_ENVIRONMENT')
)

indexes = pinecone.list_indexes()

def get_index_from_context(context):
  if context == 'sender':
    index = pinecone.Index('sender-information')
  elif context == 'voter':
    index = pinecone.Index('voter-information')
  elif context == 'general':
    index = pinecone.Index('general-information')
  else:
    raise Exception(f'Invalid context: {context}')
  return index
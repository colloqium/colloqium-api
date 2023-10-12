import os
import tiktoken
import openai
import pinecone
import uuid


tokenizer = tiktoken.get_encoding('gpt2')

EMBEDDINGS_MODEL = "text-embedding-ada-002"
INDEX_DIMENSIONS = 1536 # specific for "text-embedding-ada-002" model

pinecone.init(
    api_key = os.getenv('PINECONE_API_KEY'),
    environment = os.getenv('PINECONE_ENVIRONMENT')
)

indexes = pinecone.list_indexes()


def get_embeddings_vector(string):
  res = openai.Embedding.create(input=[string], engine=EMBEDDINGS_MODEL)
  embeds = [record['embedding'] for record in res['data']]
  print(f'Generated embeddings for the string "{string[0:100]}", dimensions: {len(embeds[0])}')
  return embeds


def get_vector_id(meta):
  '''
    meta: Dictionary that contains the metadata for the vector. Should include the context and id.

    e.g. meta = {
        'context': 'sender',
        'id': '1234',
        'text': 'This is the text that will be used to generate the vector',
    }
  '''
  vector_id_part1 = meta['context']
  vector_id_part2 = meta['id']
  # get a random uuid to add to the end of the vector id to avoid collisions
  vector_id_part3 = str(uuid.uuid4())
  vector_id = f'{vector_id_part1}-{vector_id_part2}-{vector_id_part3}'

  print(f'vector_id = {vector_id}')
  return vector_id

def save_vector_plus_meta(text, meta, index):
  '''
    text: String that will be used to generate the embeddings.
    meta: Dictionary that contains the metadata for the vector. Should include the context, id.
  '''
  embeds = get_embeddings_vector(text)

  meta['text'] = text


  vector_id = get_vector_id(meta)
  to_upsert = (
      vector_id,
      embeds,
      meta) # meta (source text and other fields)
  index.upsert(vectors=[to_upsert])
  print(f'Vector #{vector_id} was upserted OK')

def get_top_relevant_messages(text, index, top_k=10, similarity_threshold=0.5, metadata=None):
    embeds = get_embeddings_vector(text)

    # confirm metadata has an id, otherwise throw an error
    if metadata is None:
        raise Exception("Metadata is required")

    if 'id' not in metadata.keys():
        raise Exception("Metadata must include an id")

    res = index.query(
        embeds,
        top_k=top_k,
        filter={
        "id": int(metadata['id'])
        },
        include_metadata=True
        )

    relevance_limit = float(similarity_threshold)
    relevant_matches = []

    print("All matches:")
    for match in res["matches"]:
        print(f'-- {round(match["score"], 2)}: {match["metadata"]["text"]}')
        if match["score"] >= relevance_limit:
            print(">>>>> IT'S A MATCH!!! <<<<")
            match["metadata"]["score"] = match["score"]
            relevant_matches.append(match["metadata"])

    if len(relevant_matches) == 0:
        print("No relevant matches found")
    else:
        print("Relevant matches:")
        [print(f'-- {round(relevant_match["score"], 2)}: {relevant_match["context"]}: {relevant_match["id"]}') for relevant_match in relevant_matches]
    return relevant_matches


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
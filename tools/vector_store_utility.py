import openai
from context.vector_store import get_index_from_context, EMBEDDINGS_MODEL
from langchain.text_splitter import CharacterTextSplitter
import uuid

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
  vector_id_part3 = str(uuid.uuid4())[0:8]
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

def get_vector_store_results(query: str, top_k: int = 3, similarity_threshold: float = 0.75, metadata: dict = {}):

    '''
        Metadata should be a dictionary that contains the context and id of the vector you want to search for.

        Valid contexts are:
            sender
            voter
            general

        e.g. metadata = {
            'context': 'sender',
            'id': '1234', # where this is the Sender.id from the database
        }

    '''
    
    index = get_index_from_context(metadata['context'])
    
    embeds = get_embeddings_vector(query)

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
        current_results = get_vector_store_results(chunck, 1, 0.9999, metadata)

        if len(current_results) != 0:
            continue

        save_vector_plus_meta(chunck, metadata, index)
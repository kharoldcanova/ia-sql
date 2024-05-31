import os
import dotenv
from llama_index.core import SimpleDirectoryReader, PromptHelper, ServiceContext, VectorStoreIndex, Document
from llama_index.llms.openai import OpenAI
import pandas as pd

dotenv.load_dotenv()

def load_api_key():
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("API Key not found. Please set it in the .env file.")
    return api_key

def create_prompt_helper():
    max_input_size = 4096
    num_outputs = 2000
    chunk_overlap_ratio = 0.1 
    chunk_size_limit = 600
    return PromptHelper(max_input_size, num_outputs, chunk_overlap_ratio, chunk_size_limit=chunk_size_limit)

def create_llm(api_key):
    system_prompt = """
    Eres una herramienta que convierte las consultas en lenguaje natural en consultas SQL para MySQL. Tienes acceso a dos archivos:
    1. 'estructura': Contiene archivos que describen la estructura de las tablas de la base de datos, como el esquema y las relaciones entre las tablas.
    2. 'consultas': Contiene ejemplos de consultas SQL ya realizadas.

    Usa esta información para ayudar a generar consultas SQL precisas usando la estructura de la base de datos y modificando las consultas de ejemplo basadas en las preguntas que te hagan.
    """
    return OpenAI(
        model="gpt-3.5-turbo-1106",
        temperature=0,
        max_tokens=2000,
        openai_api_key=api_key,
        system_prompt=system_prompt,
    )
def create_index(directory_path, llm, prompt_helper):
    documents = SimpleDirectoryReader(directory_path).load_data()
    service_context = ServiceContext.from_defaults(llm=llm, prompt_helper=prompt_helper)
    return VectorStoreIndex.from_documents(documents, service_context=service_context)

def query_index(index, query):
    query_engine = index.as_query_engine()
    return query_engine.query(query)

def construct_index(path):
    try:
        api_key = load_api_key()
        prompt_helper = create_prompt_helper()
        llm = create_llm(api_key)
        index = create_index(path, llm, prompt_helper)
        if index is None:
            print("Failed to create index.")
            return
        question = input("Haz una pregunta: ")
        response = query_index(index, question)
        print(response)
    except Exception as e:
        print(f"An error occurred: {e}")

# Llama a la función con las rutas adecuadas
# construct_index("./documents/estructura", "./documents/consultas")

# Llama a la función con las rutas adecuadas
construct_index("./documents")

from langserve import add_routes
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from knowledge_base.ChatBot import RAGRetriever
from chat.models import Chat
from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import JSONResponse
from contextlib import asynccontextmanager

app = FastAPI()






def get_rag_retriever(chat_id: int):
    chat = Chat.objects.get(id=chat_id)
    rag_retriever = RAGRetriever()
    pipeline_id = chat.pipeline.id
    rag_retriever.set_custom_retriever("pipeline_chunks", "content", pipeline_id)

    return rag_retriever


def get_chat_chain(chat_id: int):
    return RAGRetriever().build_pipeline_flow()


chat_chains = {}


def get_or_create_chat_chain(chat_id: int):
    if chat_id not in chat_chains:
        chat_chains[chat_id] = get_chat_chain(chat_id)
    return chat_chains[chat_id]


# Function to invoke the chat chain
def invoke_chat(chat_id: int, data: dict):
    chain = get_or_create_chat_chain(chat_id)
    return chain.invoke(data)


# Function to stream the chat response
def stream_chat(chat_id: int, data: dict):
    chain = get_or_create_chat_chain(chat_id)
    return chain.stream(data)


# Function to get input schema
def get_input_schema(chat_id: int):
    chain = get_or_create_chat_chain(chat_id)
    return chain.input_schema.schema()


# Function to get output schema
def get_output_schema(chat_id: int):
    chain = get_or_create_chat_chain(chat_id)
    return chain.output_schema.schema()


# Function to get config schema
def get_config_schema(chat_id: int):
    chain = get_or_create_chat_chain(chat_id)
    return chain.config_schema.schema()

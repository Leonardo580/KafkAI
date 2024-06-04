import os
from asgiref.sync import async_to_sync, sync_to_async

from langchain_core.runnables.history import RunnableWithMessageHistory

from chat.models import Chat
from langchain.chains.history_aware_retriever import create_history_aware_retriever
from langchain_community.vectorstores import Weaviate
from langchain.prompts.prompt import PromptTemplate
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.chat_message_histories import ChatMessageHistory

from .weaviate_init import WeaviateConnector
from langchain_cohere.chat_models import ChatCohere
from langchain_cohere.embeddings import CohereEmbeddings
from langchain_weaviate.vectorstores import WeaviateVectorStore
from langchain.chains.retrieval import create_retrieval_chain
from django.conf import settings
from langchain.chains import ChatVectorDBChain
from langchain_community.vectorstores import Weaviate
import weaviate
from langchain_core.output_parsers import StrOutputParser
from langchain import hub
from langchain.chains.combine_documents import create_stuff_documents_chain

import asyncio


async def get_chat_history(session_id):
    msg_history = await asyncio.get_event_loop().run_in_executor(
        None, lambda: list(
            Chat.objects.get(id=session_id).messages.all().order_by('created_at').values_list('content', flat=True))
    )
    return msg_history


class RAGRetriever:
    def __init__(self):
        self.weaviate_client = WeaviateConnector().get_instance().client
        self.client = weaviate.Client(
            "http://localhost:8081",
            additional_headers={
                "X-Cohere-Api-Key": settings.COHERE_API_KEY
            }
        )
        self.retriever = Weaviate(self.client,
                                  "Knowledge_base",
                                  "answer").as_retriever()
        self.cohere_model = ChatCohere(cohere_api_key=os.getenv('COHERE_API_KEY'), truncate="AUTO")
        self.cohere_embeddings = CohereEmbeddings(cohere_api_key=os.getenv('COHERE_API_KEY'))
        self.cohere_embeddings.model = "command-r"

        # self.retriever = WeaviateVectorStore(self.weaviate_client,
        #                                      "knowledge_base",
        #                                      "question",
        #                                      embedding=self.cohere_embeddings)

        template = ""
        self.rag_weaviate = self.weaviate_client.collections.get("knowledge_base")

        # vector_store = Weaviate(
        #     client,
        #     "knowledge_base",
        #     "answer"
        # )
        # self.qa_chain = ChatVectorDBChain.from_llm(
        #     self.cohere_model,
        #     vector_store
        # )

    def get_docs(self, query):
        return self.retriever.similarity_search(query)

    # def generate_answer(self, query):
    #     try:
    #         # Set up the LangChain Weaviate retriever
    #         retriever = self.retriever
    #
    #         # Set up the prompt template for generating the answer
    #         prompt_template = """
    #             Vous êtes assistant pour les tâches de réponses aux questions. Utilisez les éléments de contexte récupérés suivants pour répondre à la question. Si vous ne connaissez pas la réponse, dites simplement que vous ne la savez pas. Utilisez trois phrases maximum et gardez la réponse concise.
    #
    #             Question: {question}
    #
    #             Context: {contexte}
    #
    #             Répondre:
    #         """
    #         # prompt = PromptTemplate(template=prompt_template)
    #         retrival_qa_template = hub.pull("langchain-ai/retrieval-qa-chat")
    #         retrival_qa_template.format(chat_history=["i am 3 years old"], context="you're a bot", input=query)
    #         combine = create_stuff_documents_chain(self.cohere_model, retrival_qa_template
    #                                                , output_parser=StrOutputParser())
    #         retieval_chain = create_retrieval_chain(self.retriever, combine)
    #
    #         # Generate the answer using the RetrievalQA chain
    #         result = retieval_chain
    #         return result
    #
    #     except Exception as e:
    #         print(e)
    #
    #     return "We are currently facing an issue with our servers. Please try again later."

    def generate_answer(self, query):
        try:
            # Set up the LangChain Weaviate retriever
            retriever = self.retriever

            # Set up the prompt template for generating the answer
            contextualize_q_system_prompt = (
                "Given a chat history and the latest user question "
                "which might reference context in the chat history, "
                "formulate a standalone question which can be understood "
                "without the chat history. Do NOT answer the question, "
                "just reformulate it if needed and otherwise return it as is."
            )
            contextualize_q_prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", contextualize_q_system_prompt),
                    MessagesPlaceholder("chat_history"),
                    ("human", "{input}"),
                ]
            )
            history_aware_retriever = create_history_aware_retriever(
                self.cohere_model, retriever, contextualize_q_prompt
            )
            system_prompt = (
                "You are an assistant for question-answering tasks. "
                "Use the following pieces of retrieved context to answer "
                "the question. If you don't know the answer, say that you "
                "don't know. Use three sentences maximum and keep the "
                "answer concise."
                "\n\n"
                "{context}"
            )

            qa_prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", system_prompt),
                    MessagesPlaceholder("chat_history"),
                    ("human", "{input}"),
                ]
            )

            # prompt = PromptTemplate(template=prompt_template)
            combine = create_stuff_documents_chain(self.cohere_model, qa_prompt
                                                   , output_parser=StrOutputParser())
            retieval_chain = create_retrieval_chain(history_aware_retriever, combine)

            return retieval_chain
        except Exception as e:
            print(e)

        return "We are currently facing an issue with our servers. Please try again later."

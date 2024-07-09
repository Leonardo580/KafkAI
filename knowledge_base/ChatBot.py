import os
from langchain_experimental.text_splitter import SemanticChunker
import requests
from asgiref.sync import async_to_sync, sync_to_async
from llama_parse import LlamaParse
from llama_index.core import SimpleDirectoryReader

from langchain_core.runnables.history import RunnableWithMessageHistory

from chat.models import Chat
from langchain.chains.history_aware_retriever import create_history_aware_retriever
from langchain_community.vectorstores import Weaviate
from langchain.prompts.prompt import PromptTemplate
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.chat_message_histories import ChatMessageHistory

from knowledge.models import Knowledge, KnowledgeFile
from .weaviate_init import WeaviateConnector
from langchain_cohere.chat_models import ChatCohere
from langchain_cohere.embeddings import CohereEmbeddings
from langchain_weaviate.vectorstores import WeaviateVectorStore
from langchain.chains.retrieval import create_retrieval_chain
from django.conf import settings
from langchain.chains import ChatVectorDBChain
from langchain_community.vectorstores import Weaviate
import weaviate
from langchain_community.retrievers.weaviate_hybrid_search import WeaviateHybridSearchRetriever
from langchain_core.output_parsers import StrOutputParser
from langchain import hub
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.prompts.few_shot import FewShotPromptTemplate
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
        # self.client = weaviate.Client(
        #     "http://localhost:8081",
        #     additional_headers={
        #         "X-Cohere-Api-Key": settings.COHERE_API_KEY
        #     }
        # )
        self.cohere_model = ChatCohere(cohere_api_key=os.getenv('COHERE_API_KEY'))

        self.cohere_embeddings = CohereEmbeddings(cohere_api_key=os.getenv('COHERE_API_KEY'))
        self.retriever = WeaviateVectorStore(self.weaviate_client, "knowledge_base", "answer"
                                             , embedding=self.cohere_embeddings).as_retriever()

        self.cohere_embeddings.model = "embed-multilingual-v3.0"
        self.ocr_url = "https://api.llamacloud.ai/v1/pdf-extract"
        self.ocr_api_key = os.getenv('OCRENGINE_API_KEY')
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

    def parse_files(self, knowledge):
        # TODO: add support for other file types
        # TODO: config the language to French
        parser = LlamaParse(
            api_key=self.ocr_api_key,
            result_type="markdown"
        )
        files = []
        for k in knowledge:
            files.extend(KnowledgeFile.objects.filter(knowledge=k))
        input_files = [f.file.path for f in files]
        file_extractor = {".pdf": parser, ".doc": parser, ".docx": parser}
        return SimpleDirectoryReader(input_files=input_files, file_extractor=file_extractor, encoding="latin-1",
                                     raise_on_error=True).load_data()

    def embed_knowledge(self, knowledge, pipeline_id, progress_callback=None):
        text_splitter = SemanticChunker(self.cohere_embeddings)
        str_docs = [d.text for d in self.parse_files(knowledge)]
        docs = text_splitter.create_documents(str_docs)
        pipeline_chunks = self.weaviate_client.collections.get("pipeline_chunks")

        total_splits = len(docs)
        with pipeline_chunks.batch.dynamic() as batch:
            for i, s in enumerate(docs):
                item = {
                    "content": s.page_content,
                    "Knowledge_id": pipeline_id
                }
                batch.add_object(item)
                # Update progress
                if progress_callback:
                    progress_callback(i + 1, total_splits)

    def generate_answer(self, query):
        try:
            # Set up the LangChain Weaviate retriever
            retriever = self.retriever

            # Set up the prompt template for generating the answer
            contextualize_q_system_prompt = (
                "Étant donné un hisorique de chat et la dernière question de l'utilisateur "
                "qui pourrait faire référence au contexte dans l'historique du chat, "
                "formulez une question autonome qui peut être comprise "
                "sans l'historique du chat. NE répondez PAS à la question, "
                "reformulez-la si nécessaire et sinon renvoyez-la telle quelle."
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
                "Vous êtes un assistant pour les tâches d'assistance technique. "
                "Utilisez les éléments de contexte récupérés et les exemples fournis pour répondre "
                "à la question. Si vous ne connaissez pas la réponse, dites-le. "
                "Utilisez trois phrases maximum et gardez la réponse concise. "
                "Répondez toujours en français."
                "\n\n"
                "Contexte :\n"
                "{context}"
            )

            qa_prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", system_prompt),
                    MessagesPlaceholder("chat_history"),
                    ("human", "{input}"),
                ]
            )

            # Formatting few-shot examples

            combine = create_stuff_documents_chain(
                self.cohere_model,
                qa_prompt,
                output_parser=StrOutputParser()

            )
            retrieval_chain = create_retrieval_chain(history_aware_retriever, combine)

            return retrieval_chain
        except Exception as e:
            print(e)

        return "Nous rencontrons actuellement un problème avec nos serveurs. Veuillez réessayer plus tard."

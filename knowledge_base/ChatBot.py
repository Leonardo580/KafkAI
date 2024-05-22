import os

from .weaviate_init import WeaviateConnector
from langchain_cohere.llms import Cohere
from langchain_cohere.embeddings import CohereEmbeddings
from langchain_weaviate.vectorstores import WeaviateVectorStore
from langchain.chains import RetrievalQA
from django.conf import settings


class RAGRetriever:
    def __init__(self):
        self.weaviate_client = WeaviateConnector().get_instance().client
        self.cohere_model = Cohere(cohere_api_key=os.getenv('COHERE_API_KEY'))
        self.cohere_embeddings = CohereEmbeddings(cohere_api_key=os.getenv('COHERE_API_KEY'))
        self.cohere_embeddings.model = "embed-multilingual-v3.0"

        self.retriever = WeaviateVectorStore(self.weaviate_client,
                                             "knowledge_base",
                                             "question",
                                             embedding=self.cohere_embeddings)

        template = ""
        self.qa_chain = RetrievalQA.from_chain_type(
            retriever=self.retriever.as_retriever(search_type="mmr"),
            llm=self.cohere_model
        )

        self.rag_weaviate = self.weaviate_client.collections.get("knowledge_base")

    def get_docs(self, query):
        return self.retriever.similarity_search(query)

    def generate_answer(self, query):
        try:
            response = self.rag_weaviate.query.near_text(
                query,
                limit=1,
                # grouped_task="regenerate the answer to be more human readable"
            ).generated
            print(response)

            # return response.objects[0].properties["answer"]
        except Exception as e:
            print(e)

        return "We are currently facing an issue with our servers. Please try again later."

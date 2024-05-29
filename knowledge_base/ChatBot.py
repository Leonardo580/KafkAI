import os

from .weaviate_init import WeaviateConnector
from langchain_cohere.llms import Cohere
from langchain_cohere.embeddings import CohereEmbeddings
from langchain_weaviate.vectorstores import WeaviateVectorStore
from langchain.chains import RetrievalQA
from django.conf import settings
from langchain.chains import ChatVectorDBChain
from langchain_community.vectorstores import Weaviate
import weaviate


class RAGRetriever:
    def __init__(self):
        self.weaviate_client = WeaviateConnector().get_instance().client
        self.cohere_model = Cohere(cohere_api_key=os.getenv('COHERE_API_KEY'))
        self.cohere_embeddings = CohereEmbeddings(cohere_api_key=os.getenv('COHERE_API_KEY'))
        self.cohere_embeddings.model = "command-r"

        # self.retriever = WeaviateVectorStore(self.weaviate_client,
        #                                      "knowledge_base",
        #                                      "question",
        #                                      embedding=self.cohere_embeddings)

        template = ""
        self.rag_weaviate = self.weaviate_client.collections.get("knowledge_base")
        self.client = weaviate.Client(
            "http://localhost:8081",
            additional_headers={
                "X-Cohere-Api-Key": settings.COHERE_API_KEY
            }
        )
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

    def generate_answer(self, query):
        try:
            response = self.rag_weaviate.generate.near_text(
                query,
                single_prompt="regenerate the answer to be more human readable {answer}",
                limit=3,
                distance=0.5,
                grouped_task="summarize into bullet point"

            ).generated
            if response is None:

                response = self.cohere_model.generate(
                    prompts=["speak only in french", f"répondez à la question vos connaissances en français: {query}"], max_tokens=200)
                response = response.generations[0][0].text

            # response = self.client.query.get(
            #     "knowledge_base",
            #     ["subject", "question", "answer"]
            # ).with_near_text({
            #     "concepts": [query]
            # }).with_limit(2).with_additional([
            #     "distance"
            # ]).do()

            return str(response)
        except Exception as e:
            print(e)

        return "We are currently facing an issue with our servers. Please try again later."

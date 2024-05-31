import os
from langchain_community.vectorstores import Weaviate
from langchain.prompts.prompt import PromptTemplate
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
                                  "question").as_retriever()
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

    def generate_answer(self, query):
        try:
            # Set up the LangChain Weaviate retriever
            retriever = self.retriever

            # Set up the prompt template for generating the answer
            prompt_template = """

            Instructions: regenerate the answer to be more human readable, summarize into bullet points, and limit the answer to 3 key points.

            Answer:
            """
            # prompt = PromptTemplate(template=prompt_template)
            retrival_qa_template = hub.pull("langchain-ai/retrieval-qa-chat")
            combine = create_stuff_documents_chain(self.cohere_model, retrival_qa_template
                                                   , output_parser=StrOutputParser())
            retieval_chain = create_retrieval_chain(self.retriever, combine)

            # Generate the answer using the RetrievalQA chain
            result = retieval_chain
            return result

        except Exception as e:
            print(e)

        return "We are currently facing an issue with our servers. Please try again later."

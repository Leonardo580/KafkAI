import os
from pprint import pprint
from langgraph.graph import END, StateGraph, START
from langchain.tools.retriever import create_retriever_tool
# from langchain.tools.tavily_search import TavilySearchResults
# from langchain.utilities.tavily_search import TavilySearchAPIWrapper
from langchain_community.retrievers import TavilySearchAPIRetriever
from langchain.schema import Document
from typing import List
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.messages import HumanMessage
from pydantic import SecretStr
from typing_extensions import TypedDict
from langchain_core.runnables import RunnablePassthrough
from langchain_experimental.text_splitter import SemanticChunker
from weaviate.classes.query import Filter

import requests
from asgiref.sync import async_to_sync, sync_to_async
from llama_parse import LlamaParse
from llama_index.core import SimpleDirectoryReader

from langchain_core.runnables.history import RunnableWithMessageHistory
from weaviate.collections.classes.grpc import MetadataQuery

from chat.models import Chat
from langchain.chains.history_aware_retriever import create_history_aware_retriever
from langchain_community.vectorstores import Weaviate
from langchain.prompts.prompt import PromptTemplate
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.chat_message_histories import ChatMessageHistory

from knowledge.models import Knowledge, KnowledgeFile
from .weaviate_init import WeaviateConnector
from langchain_cohere import ChatCohere
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
        preamble = """
                    Vous êtes un assistant pour les tâches d'assistance technique. 
                    Utilisez trois phrases maximum et gardez la réponse concise. 
                    Répondez toujours en français.
                    """
        self.cohere_model = (ChatCohere(model="command-r"
                                        , tempreature=0.2
                                        , cohere_api_key=os.getenv('COHERE_API_KEY'))
                             .bind(preamble=preamble))

        rag_preamble = """
                    Vous êtes un assistant pour les tâches d'assistance technique. 
                    Utilisez les éléments de contexte récupérés et les exemples fournis pour répondre 
                    à la question. Si vous ne connaissez pas la réponse, dites-le. 
                    Utilisez trois phrases maximum et gardez la réponse concise. 
                    Répondez toujours en français.
        """
        self.rag_cohere_model = (ChatCohere(model="command-r"
                                            , tempreature=0.2
                                            , cohere_api_key=os.getenv('COHERE_API_KEY'))
                                 .bind(preamble=rag_preamble))

        grad_preamble = """You are a grader assessing relevance of a retrieved document to a user question. \n
        If the document contains keyword(s) or semantic meaning related to the user question, grade it as relevant. \n
        Give a binary score 'yes' or 'no' score to indicate whether the document is relevant to the question."""
        self.grad_llm = ChatCohere(model="command-r", temprature=0, cohere_api_key=os.getenv('COHERE_API_KEY'))
        structured_llm_grader = self.grad_llm.with_structured_output(GradeDocuments, preamble=grad_preamble)
        grad_prompt = ChatPromptTemplate.from_messages(
            [("human", "Retrieved document: \n\n {document} \n\n User question: {question}"), ]
        )
        route_preamble = """You are an expert at routing a user question to a vectorstore or web search.
        The vectorstore contains documents related to agents, prompt engineering, and adversarial attacks.
        Use the vectorstore for questions on these topics. Otherwise, use web-search."""
        self.route_llm = ChatCohere(model="command-r", temprature=0, cohere_api_key=os.getenv('COHERE_API_KEY'))
        route_prompt = ChatPromptTemplate.from_messages(
            ("human", "{question}"),
        )
        preamble = """You are a grader assessing whether an LLM generation is grounded in / supported by a set of retrieved facts. \n
        Give a binary score 'yes' or 'no'. 'Yes' means that the answer is grounded in / supported by the set of facts."""
        self.hallucination_llm = ChatCohere(model="command-r", temprature=0, cohere_api_key=os.getenv('COHERE_API_KEY'))
        structured_llm_hallucination = self.hallucination_llm.with_structured_output(
            GradeDocuments, preamble=preamble
        )
        hallucination_prompt = ChatPromptTemplate.from_messages(
            ("human", "Set of facts: \n\n {documents} \n\n LLM generation: {generation}"),
        )
        preamble = """You are a grader assessing whether an answer addresses / resolves a question \n
        Give a binary score 'yes' or 'no'. Yes' means that the answer resolves the question."""
        self.answer_grader_llm = ChatCohere(model="command-r", temprature=0, cohere_api_key=os.getenv('COHERE_API_KEY'))
        structured_llm_answer_grader = self.answer_grader_llm.with_structured_output(
            GradeAnswer, preamble=preamble
        )
        answer_prompt = ChatPromptTemplate.from_messages(
            [
                ("human", "User question: \n\n {question} \n\n LLM generation: {generation}"),
            ]
        )

        self.cohere_embeddings = CohereEmbeddings(cohere_api_key=os.getenv('COHERE_API_KEY'))

        self.cohere_embeddings.model = "embed-multilingual-v3.0"
        self.ocr_url = "https://api.llamacloud.ai/v1/pdf-extract"
        self.ocr_api_key = os.getenv('OCRENGINE_API_KEY')
        self.retriever = WeaviateVectorStore(self.weaviate_client,
                                             "pipeline_chunks",
                                             "content",
                                             embedding=self.cohere_embeddings)

        retiever_tool = create_retriever_tool(
            self.retriever.as_retriever(),
            "retrieve_from_weaviate",
            "Search and return the docs from submitted pdf",
        )
        structured_llm_route = self.route_llm.bind_tools(
            tools=[web_search, retiever_tool], preamble=route_preamble
        )
        self.rag_weaviate = self.weaviate_client.collections.get("knowledge_base")
        self.llm_chain = self.prompt | self.cohere_model | StrOutputParser()
        self.rag_chain = self.rag_prompt | self.rag_cohere_model | StrOutputParser()
        self.retrieval_grader = grad_prompt | structured_llm_grader
        self.web_search_tool = TavilySearchAPIRetriever(api_key=os.getenv('TAVILY_API_KEY'))
        self.question_router = route_prompt | structured_llm_route
        self.hallucination_grader = hallucination_prompt | structured_llm_hallucination
        self.answer_grader = answer_prompt | structured_llm_answer_grader

    def prompt(self, x):
        return ChatPromptTemplate.from_messages(
            [HumanMessage(f"Question: {x['question']} \nAnswer: ")]
        )

    def rag_prompt(self, x):
        return ChatPromptTemplate.from_messages(
            [
                HumanMessage(
                    f"Question: {x['question']} \nAnswer: ",
                    additional_kwargs={"documents": x["documents"]},
                )
            ]
        )

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

    def get_context(self, collection_name, query, pipeline_id):
        try:
            pipeline_chunks = self.weaviate_client.collections.get(collection_name)
            context = pipeline_chunks.query.hybrid(
                query=query,
                alpha=0.5,
                filters=Filter.by_property("knowledge_id").equal(pipeline_id),
                return_metadata=MetadataQuery(score=True, explain_score=True),
                auto_limit=2,
                # limit=5
            )

            return "\n".join([obj.properties['content'] for obj in context.objects])

        except Exception as e:
            print(e)

    def set_custom_retriever(self, index_name, text_name, filters=None):
        self.retriever = WeaviateVectorStore(self.weaviate_client, index_name, text_name
                                             , embedding=self.cohere_embeddings).as_retriever(
            search_kwargs={"filters": filters}
        )

    def generate_answer(self):
        try:
            retriever = self.retriever
            prompt = hub.pull("rlm/rag-prompt")

            format_doc = lambda docs: "\n\n".join([d.page_content for d in docs])
            rag_chain = (
                    {"context": retriever, "question": RunnablePassthrough()}
                    | prompt
                    | self.cohere_model
                    | StrOutputParser()
            )
            return rag_chain
        except Exception as e:
            print(e)

        return "Nous rencontrons actuellement un problème avec nos serveurs. Veuillez réessayer plus tard."

    def retrieve(self, state):

        """
        Retrieve documents

        Args:
            state (dict): The current graph state

        Returns:
            state (dict): New key added to state, documents, that contains retrieved documents
        """
        question = state["question"]

        # Retrieval
        documents = self.retriever.as_retriever().invoke(question)
        return {"documents": documents, "question": question}

    def llm_fallback(self, state):
        """
        Generate answer using the LLM w/o vectorstore

        Args:
            state (dict): The current graph state

        Returns:
            state (dict): New key added to state, generation, that contains LLM generation
        """
        print("---LLM Fallback---")
        question = state["question"]
        generation = self.llm_chain.invoke({"question": question})
        return {"question": question, "generation": generation}

    def generate(self, state):
        """
        Generate answer using the vectorstore

        Args:
            state (dict): The current graph state

        Returns:
            state (dict): New key added to state, generation, that contains LLM generation
        """
        print("---GENERATE---")
        question = state["question"]
        documents = state["documents"]
        if not isinstance(documents, list):
            documents = [documents]

        # RAG generation
        generation = self.rag_chain.invoke({"documents": documents, "question": question})
        return {"documents": documents, "question": question, "generation": generation}

    def grade_documents(self, state):
        """
        Determines whether the retrieved documents are relevant to the question.

        Args:
            state (dict): The current graph state

        Returns:
            state (dict): Updates documents key with only filtered relevant documents
        """

        print("---CHECK DOCUMENT RELEVANCE TO QUESTION---")
        question = state["question"]
        documents = state["documents"]

        # Score each doc
        filtered_docs = []
        for d in documents:
            score = self.retrieval_grader.invoke(
                {"question": question, "document": d.page_content}
            )
            grade = "yes"
            if score:
                grade = score.binary_score
            if grade == "yes":
                print("---GRADE: DOCUMENT RELEVANT---")
                filtered_docs.append(d)
            else:
                print("---GRADE: DOCUMENT NOT RELEVANT---")
                continue
        return {"documents": filtered_docs, "question": question}

    def web_search(self, state):
        """
        Web search based on the re-phrased question.

        Args:
            state (dict): The current graph state

        Returns:
            state (dict): Updates documents key with appended web results
        """

        print("---WEB SEARCH---")
        question = state["question"]

        # Web search
        docs = self.web_search_tool.invoke(question)
        web_results = "\n".join([d["content"] for d in docs])
        web_results = Document(page_content=web_results)

        return {"documents": web_results, "question": question}

    ### Edges ###

    def route_question(self, state):
        """
        Route question to web search or RAG.

        Args:
            state (dict): The current graph state

        Returns:
            str: Next node to call
        """

        print("---ROUTE QUESTION---")
        question = state["question"]
        source = self.question_router.invoke({"question": question})

        # Fallback to LLM or raise error if no decision
        if "tool_calls" not in source.additional_kwargs:
            print("---ROUTE QUESTION TO LLM---")
            return "llm_fallback"
        if len(source.additional_kwargs["tool_calls"]) == 0:
            raise "Router could not decide source"

        # Choose datasource
        datasource = source.additional_kwargs["tool_calls"][0]["function"]["name"]
        if datasource == "web_search":
            print("---ROUTE QUESTION TO WEB SEARCH---")
            return "web_search"
        elif datasource == "vectorstore":
            print("---ROUTE QUESTION TO RAG---")
            return "vectorstore"
        else:
            print("---ROUTE QUESTION TO LLM---")
            return "vectorstore"

    def decide_to_generate(self, state):
        """
        Determines whether to generate an answer, or re-generate a question.

        Args:
            state (dict): The current graph state

        Returns:
            str: Binary decision for next node to call
        """

        print("---ASSESS GRADED DOCUMENTS---")
        # state["question"]
        filtered_documents = state["documents"]

        if not filtered_documents:
            # All documents have been filtered check_relevance
            # We will re-generate a new query
            print("---DECISION: ALL DOCUMENTS ARE NOT RELEVANT TO QUESTION, WEB SEARCH---")
            return "web_search"
        else:
            # We have relevant documents, so generate answer
            print("---DECISION: GENERATE---")
            return "generate"

    def grade_generation_v_documents_and_question(self, state):
        """
        Determines whether the generation is grounded in the document and answers question.

        Args:
            state (dict): The current graph state

        Returns:
            str: Decision for next node to call
        """

        print("---CHECK HALLUCINATIONS---")
        question = state["question"]
        documents = state["documents"]
        generation = state["generation"]

        score = self.hallucination_grader.invoke(
            {"documents": documents, "generation": generation}
        )
        grade = "yes"
        if score:
            grade = score.binary_score

        # Check hallucination
        if grade == "yes":
            print("---DECISION: GENERATION IS GROUNDED IN DOCUMENTS---")
            # Check question-answering
            print("---GRADE GENERATION vs QUESTION---")
            score = self.answer_grader.invoke({"question": question, "generation": generation})
            grade = "yes"
            if score:
                grade = score.binary_score
            if grade == "yes":
                print("---DECISION: GENERATION ADDRESSES QUESTION---")
                return "useful"
            else:
                print("---DECISION: GENERATION DOES NOT ADDRESS QUESTION---")
                return "not useful"
        else:
            pprint("---DECISION: GENERATION IS NOT GROUNDED IN DOCUMENTS, RE-TRY---")
            return "not supported"

    def build_pipeline_flow(self):
        workflow = StateGraph(GraphState)
        workflow.add_node("web_search", self.web_search)  # web search
        workflow.add_node("retrieve", self.retrieve)  # retrieve
        workflow.add_node("grade_documents", self.grade_documents)  # grade documents
        workflow.add_node("generate", self.generate)  # rag
        workflow.add_node("llm_fallback", self.llm_fallback)  # llm

        # Build graph
        workflow.add_conditional_edges(
            START,
            self.route_question,
            {
                "web_search": "web_search",
                "vectorstore": "retrieve",
                "llm_fallback": "llm_fallback",
            },
        )
        workflow.add_edge("web_search", "generate")
        workflow.add_edge("retrieve", "grade_documents")
        workflow.add_conditional_edges(
            "grade_documents",
            self.decide_to_generate,
            {
                "web_search": "web_search",
                "generate": "generate",
            },
        )
        workflow.add_conditional_edges(
            "generate",
            self.grade_generation_v_documents_and_question,
            {
                "not supported": "generate",  # Hallucinations: re-generate
                "not useful": "web_search",  # Fails to answer question: fall-back to web-search
                "useful": END,
            },
        )
        workflow.add_edge("llm_fallback", END)

        # Compile
        app = workflow.compile()
        print("compiled successfully")
        return app

class GraphState(TypedDict):
    """|
    Represents the state of our graph.

    Attributes:
        question: question
        generation: LLM generation
        documents: list of documents
    """

    question: str
    generation: str
    documents: List[str]


class GradeDocuments(BaseModel):
    """Binary score for relevance check on retrieved documents."""

    binary_score: str = Field(
        description="Documents are relevant to the question, 'yes' or 'no'"
    )


class web_search(BaseModel):
    """
    The internet. Use web_search for questions that are related to anything else than agents, prompt engineering, and adversarial attacks.
    """

    query: str = Field(description="The query to use when searching the internet.")


class vectorstore(BaseModel):
    """
    A vectorstore containing documents related to agents, prompt engineering, and adversarial attacks. Use the vectorstore for questions on these topics.
    """

    query: str = Field(description="The query to use when searching the vectorstore.")


class GradeHallucinations(BaseModel):
    """Binary score for hallucination present in generation answer."""

    binary_score: str = Field(
        description="Answer is grounded in the facts, 'yes' or 'no'"
    )


class GradeAnswer(BaseModel):
    """Binary score to assess answer addresses question."""

    binary_score: str = Field(
        description="Answer addresses the question, 'yes' or 'no'"
    )

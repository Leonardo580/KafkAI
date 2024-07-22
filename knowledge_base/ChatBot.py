import os
from pprint import pprint
from langchain.chains.history_aware_retriever import create_history_aware_retriever
from langchain_core.runnables.graph import CurveStyle, MermaidDrawMethod, NodeColors
from langgraph.checkpoint.aiosqlite import AsyncSqliteSaver
from django.conf import settings
from psycopg_pool import AsyncConnectionPool
from langchain.retrievers import MergerRetriever
import pymysql
import aiomysql
from langchain_community.utilities.tavily_search import TavilySearchAPIWrapper
from langgraph.graph import END, StateGraph, START
from langchain.tools.retriever import create_retriever_tool
# from langchain.tools.tavily_search import TavilySearchResults
# from langchain.utilities.tavily_search import TavilySearchAPIWrapper
from langchain_community.retrievers import TavilySearchAPIRetriever
from langchain.schema import Document
from typing import List, Optional, Tuple
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.messages import HumanMessage, AIMessage
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
from .postgres_saver import PostgresSaver
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
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain import hub
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.prompts.few_shot import FewShotPromptTemplate
import asyncio


async def get_chat_history(session_id, k=10):
    msg_history = await asyncio.get_event_loop().run_in_executor(
        None, lambda: list(
            Chat.objects.get(id=session_id).messages.all()
            .order_by('-created_at')[:k]  # Get 10 most recent messages
            .values_list('sender', 'content')
        )
    )

    return list(map(process_chat_history, reversed(msg_history)))


def process_chat_history(msg):
    if msg[0] == "user":
        return HumanMessage(content=msg[1])
    else:
        return AIMessage(content=msg[1])


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

        grad_preamble = """Vous êtes un évaluateur évaluant la pertinence d'un document récupéré par rapport à une question d'utilisateur. \n
        Si le document contient des mots-clés ou une signification sémantique liés à la question de l'utilisateur, évaluez-le comme pertinent. \n
        Donnez une note binaire 'yes' ou 'no' pour indiquer si le document est pertinent par rapport à la question."""
        self.grad_llm = ChatCohere(model="command-r", temprature=0, cohere_api_key=os.getenv('COHERE_API_KEY'))
        structured_llm_grader = self.grad_llm.with_structured_output(GradeDocuments, preamble=grad_preamble)
        grad_prompt = ChatPromptTemplate.from_messages(
            [("human", "Document récupéré : \n\n {document} \n\n Question de l'utilisateur : {question}"), ]
        )
        self.route_preamble = """Prendre en compte l'historique de la conversation.Vous êtes un expert en routage de questions utilisateur vers un vectorstore ou une recherche Web.
        Le vectorstore contient des documents liés aux agents, à l'ingénierie des invites et aux attaques adversariales.
        Utilisez le vectorstore pour les questions sur ces sujets. Sinon, utilisez la recherche Web."""
        self.route_llm = ChatCohere(model="command-r", temprature=0, cohere_api_key=os.getenv('COHERE_API_KEY'))
        history_prompt = """
        Étant donné un historique de conversation et la dernière question de l'utilisateur qui pourrait se référer au contexte de l'historique de conversation,
         formulez une question autonome qui peut être comprise sans l'historique de conversation. 
         Ne répondez PAS à la question, reformulez-la seulement si nécessaire et sinon, renvoyez-la telle quelle.
        """
        contextualize_q_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", history_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )

        route_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", history_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{question}"),
            ]
        )
        preamble = """Vous êtes un évaluateur évaluant si une génération LLM est fondée sur / soutenue par un ensemble de faits récupérés. \n
        Donnez une note binaire 'yes' ou 'no'. 'yes' signifie que la réponse est fondée sur / soutenue par l'ensemble des faits."""
        self.hallucination_llm = ChatCohere(model="command-r", temprature=0, cohere_api_key=os.getenv('COHERE_API_KEY'))
        structured_llm_hallucination = self.hallucination_llm.with_structured_output(
            GradeDocuments, preamble=preamble
        )
        hallucination_prompt = ChatPromptTemplate.from_messages(
            ("human", "Ensemble de faits : \n\n {documents} \n\n Génération LLM : {generation}"),
        )
        preamble = """Vous êtes un évaluateur évaluant si une réponse répond / résout une question \n
        Donnez une note binaire 'yes' ou 'no'. 'yes' signifie que la réponse résout la question."""
        self.answer_grader_llm = ChatCohere(model="command-r", temprature=0, cohere_api_key=os.getenv('COHERE_API_KEY'))
        structured_llm_answer_grader = self.answer_grader_llm.with_structured_output(
            GradeAnswer, preamble=preamble
        )
        answer_prompt = ChatPromptTemplate.from_messages(
            [
                ("human", "Question de l'utilisateur : \n\n {question} \n\n Génération LLM : {generation}"),
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

        self.base_retriever = WeaviateVectorStore(self.weaviate_client,
                                                  "knowledge_base",
                                                  "answer",
                                                  embedding=self.cohere_embeddings)

        self._update_structured_llm_route()
        self.history_aware_retriever = create_history_aware_retriever(
            self.cohere_model, self.retriever.as_retriever(), contextualize_q_prompt
        )

        self.rag_weaviate = self.weaviate_client.collections.get("knowledge_base")
        self.llm_chain = self.prompt | self.cohere_model | StrOutputParser()
        self.rag_chain = self.rag_prompt | self.rag_cohere_model | StrOutputParser()
        self.retrieval_grader = grad_prompt | structured_llm_grader
        self.web_search_tool = TavilySearchResults()
        self.web_search_tool.api_wrapper = TavilySearchAPIWrapper()

        self.question_router = route_prompt | self.structured_llm_route
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

    def update_retriever(self, index_name, text_name, filters=None):
        self.retriever = WeaviateVectorStore(self.weaviate_client, index_name, text_name,
                                             embedding=self.cohere_embeddings)
        self._update_structured_llm_route(filters)

    def _update_structured_llm_route(self, filters=None):
        merged_retreiver = MergerRetriever(
            retrievers=[self.base_retriever.as_retriever(),
                        self.retriever.as_retriever(search_kwargs={"filters": filters}), ])
        retriever_tool = create_retriever_tool(
            merged_retreiver,
            "retrieve_from_weaviate",
            "Recherchez et renvoyez les documents du PDF soumis",
        )
        self.structured_llm_route = self.route_llm.bind_tools(
            tools=[web_search, retriever_tool], preamble=self.route_preamble
        )

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
        print("---LLM Fallback---")
        question = state["question"]
        chat_history = state["chat_history"]

        # Include chat history in the prompt
        # history_str = "\n".join([f"Human: {h[0]}\nAI: {h[1]}" for h in chat_history])
        prompt = f"Chat History:\n{chat_history}\n\nCurrent Question: {question}\n\nAnswer:"

        generation = self.llm_chain.invoke({"question": prompt})

        # Update chat history
        updated_history = chat_history + [(question, generation)]

        return {"question": question, "generation": generation, "chat_history": updated_history}

    def generate(self, state):
        print("---GENERATE---")
        question = state["question"]
        documents = state["documents"]
        chat_history = state["chat_history"]

        if not isinstance(documents, list):
            documents = [documents]

        # Include chat history in the prompt
        # history_str = "\n".join([f"Human: {h[0]}\nAI: {h[1]}" for h in chat_history])
        prompt = f"Chat History:\n{chat_history}\n\nCurrent Question: {question}\n\nRelevant Documents:\n{documents}\n\nAnswer:"

        generation = self.rag_chain.invoke({"documents": documents, "question": prompt})

        # Update chat history
        updated_history = chat_history + [(question, generation)]

        return {"documents": documents, "question": question, "generation": generation, "chat_history": updated_history}

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
            grade = "no"
            print(f"score : {score}")
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
        docs = self.web_search_tool.invoke({"query": question})
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

        print(f"---ROUTE QUESTION---{state}")
        question = state["question"]
        # print("*****************************",
        #       self.history_aware_retriever.invoke({"input": question, "chat_history": state["chat_history"]}))
        source = self.question_router.invoke({"question": question, "chat_history": state["chat_history"]})

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
        print(state["generation"])
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

    async def build_pipeline_flow(self):
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

        memory = AsyncSqliteSaver.from_conn_string(":memory:")
        app = workflow.compile(checkpointer=memory)
        print("compiled successfully")
        return app


class GraphState(TypedDict):
    question: str
    documents: Optional[List[Document]]
    generation: Optional[str]
    chat_history: List[Tuple[str, str]]


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


class LangGraphSingleton:
    _instance = None

    @staticmethod
    def get_instance():
        if LangGraphSingleton._instance is None:
            LangGraphSingleton()

        return LangGraphSingleton._instance

    def __init__(self):
        if LangGraphSingleton._instance is not None:
            raise Exception("This class is a singleton!")
        else:
            self.rag_retriever = RAGRetriever()
            LangGraphSingleton._instance = self

    async def initialize(self):
        self.app = await self.rag_retriever.build_pipeline_flow()

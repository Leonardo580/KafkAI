import os
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt.chat_agent_executor import AgentState
from typing_extensions import TypedDict
from langchain_cohere import CohereEmbeddings, ChatCohere
from langgraph.prebuilt import ToolNode
from langchain.chains.history_aware_retriever import create_history_aware_retriever
from langchain.retrievers import MergerRetriever
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.utilities.tavily_search import TavilySearchAPIWrapper
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from langchain_core.tools import create_retriever_tool
from langchain_experimental.llms.ollama_functions import OllamaFunctions, convert_to_ollama_tool
from langchain_weaviate import WeaviateVectorStore

from .ChatBot import RAGRetriever, GradeDocuments, GradeAnswer, RAGPipeline, web_search
from .weaviate_init import WeaviateConnector


class LocalChatBot(RAGPipeline):
    def __init__(self, config):
        # Load the configuration from the database

        assert config.llm_provider == 'huggingface'
        self.llm_model = ChatOllama(model=config.model_name)

        preamble = config.model_preamble
        self.cohere_model = self.llm_model.bind(preamble=preamble)

        rag_preamble = config.model_preamble
        self.rag_cohere_model = self.llm_model.bind(preamble=rag_preamble)

        grad_preamble = config.grade_preamble
        self.grad_llm = self.llm_model
        # structured_llm_grader = self.grad_llm.with_structured_output(GradeDocuments, preamble=grad_preamble)
        # structured_llm_grader = self.grad_llm.with_structured_output(GradeDocuments)
        # grad_prompt = ChatPromptTemplate.from_messages(
        #     [("human", config.grade_prompt), ]
        # )

        self.route_preamble = config.route_question_preamble
        self.route_llm = self.llm_model
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

        prompt = PromptTemplate(
            template="""Vous êtes un évaluateur qui détermine la pertinence d'un document récupéré par rapport à une question utilisateur. \n
Voici le document récupéré : \n\n {document} \n\n
Voici la question de l'utilisateur : {question} \n
Si le document contient des mots-clés liés à la question de l'utilisateur, évaluez-le comme pertinent. \n
Il n'est pas nécessaire que ce soit un test rigoureux. L'objectif est de filtrer les récupérations erronées. \n
Donnez une note binaire 'oui' ou 'non' pour indiquer si le document est pertinent pour la question. \n
Fournissez la note binaire sous forme de JSON avec une seule clé 'score' sans préambule ni explication.""",
            input_variables=["question", "document"],
        )

        hallucination_preamble = config.hallucination_preamble
        self.hallucination_llm = self.llm_model
        # structured_llm_hallucination = self.hallucination_llm.with_structured_output(
        #     # GradeDocuments, preamble=hallucination_preamble
        #     GradeDocuments
        # )
        hallucination_prompt = ChatPromptTemplate.from_messages(
            ("human", config.hallucination_prompt),
        )

        answer_preamble = config.answer_preamble
        self.answer_grader_llm = self.llm_model
        # structured_llm_answer_grader = self.answer_grader_llm.with_structured_output(
        #     # GradeAnswer, preamble=answer_preamble
        #     GradeAnswer
        # )
        answer_prompt = ChatPromptTemplate.from_messages(
            [
                ("human", config.answer_prompt),
            ]
        )

        assert config.embedding_provider == 'huggingface'
        self.embeddings_model = CohereEmbeddings(cohere_api_key=os.getenv('COHERE_API_KEY'))
        self.embeddings_model.model = "embed-multilingual-v3.0"
        self.ocr_url = config.ocr_url
        self.ocr_api_key = config.ocr_api_key
        self.weaviate_client = WeaviateConnector().get_instance().client

        self.retriever = WeaviateVectorStore(self.weaviate_client,
                                             "pipeline_chunks",
                                             "content",
                                             embedding=self.embeddings_model)

        self.base_retriever = WeaviateVectorStore(self.weaviate_client,
                                                  "knowledge_base",
                                                  "answer",
                                                  embedding=self.embeddings_model)

        # self._update_structured_llm_route()
        self.history_aware_retriever = create_history_aware_retriever(
            self.cohere_model, self.retriever.as_retriever(), contextualize_q_prompt
        )

        self.rag_weaviate = self.weaviate_client.collections.get("knowledge_base")
        self.llm_chain = self.prompt | self.cohere_model | StrOutputParser()
        self.rag_chain = self.rag_prompt | self.rag_cohere_model | StrOutputParser()
        # self.retrieval_grader = grad_prompt | self.llm_model | StrOutputParser()
        self.web_search_tool = TavilySearchResults()
        self.web_search_tool.api_wrapper = TavilySearchAPIWrapper()

        self.question_router = route_prompt | self.llm_model | StrOutputParser()
        self.hallucination_grader = hallucination_prompt | self.llm_model | StrOutputParser()
        self.answer_grader = answer_prompt | self.llm_model | StrOutputParser()

    def prompt(self, x):
        return ChatPromptTemplate.from_messages(
            [HumanMessage(f"Question : {x['question']} \nRéponse : ")]
        )

    def rag_prompt(self, x):
        return ChatPromptTemplate.from_messages(
            [
                HumanMessage(
                    f"Question : {x['question']} \nRéponse : ",
                    additional_kwargs={"documents": x["documents"]},
                )
            ]
        )

    def update_retriever(self, index_name, text_name, filters=None):
        self.retriever = WeaviateVectorStore(self.weaviate_client, index_name, text_name,
                                             embedding=self.embeddings_model)
        self._update_structured_llm_route(filters)

    def _update_structured_llm_route(self, filters=None):
        self.retriever = MergerRetriever(
            retrievers=[self.base_retriever.as_retriever(),
                        self.retriever.as_retriever(search_kwargs={"filters": filters}), ])

    def retrieve_docs(self, state: AgentState):
        question = state["question"]
        documents = self.retriever.get_relevant_documents(query=question)
        print("DOCUMENTS RETRIEVÉS:", documents)
        state["documents"] = [doc.page_content for doc in documents]
        return state

    def question_classifier(self, state: AgentState):
        state = self.retrieve_docs(state)
        question = state["question"]
        documents = state["documents"]
        prompt = PromptTemplate(
            template="""Vous êtes un évaluateur qui détermine la pertinence d'un document récupéré par rapport à une question utilisateur. \n 
            Voici le document récupéré : \n\n {documents} \n\n
            Voici la question de l'utilisateur : {question} \n
            Si le document contient des mots-clés liés à la question de l'utilisateur, évaluez-le comme pertinent. \n
            Il n'est pas nécessaire que ce soit un test rigoureux. L'objectif est de filtrer les récupérations erronées. \n
            Donnez une note binaire 'oui' ou 'non' pour indiquer si le document est pertinent pour la question. \n
            Fournissez la note binaire sous forme de JSON avec une seule clé 'score' sans préambule ni explication.""",
            input_variables=["question", "documents"],
        )
        llm = self.llm_model
        structured_llm = llm.with_structured_output(GradeQuestion)
        grader_llm = prompt | structured_llm
        result = grader_llm.invoke({"question": question, "documents": documents})
        print(f"QUESTION et NOTE : {question} - {result.score}")
        state["on_topic"] = result.score
        return state

    def on_topic_router(self, state: AgentState):
        on_topic = state["on_topic"]
        if on_topic.lower() == "oui":
            return "on_topic"
        return "off_topic"

    def llm_fallback(self, state):
        print("---LLM Fallback---")
        question = state["question"]
        # chat_history = state["chat_history"]

        # Include chat history in the prompt
        # history_str = "\n".join([f"Human: {h[0]}\nAI: {h[1]}" for h in chat_history])
        # prompt = f"Chat History:\n{chat_history}\n\nCurrent Question: {question}\n\nAnswer:"

        generation = self.llm_chain.invoke({"question": question})

        # Update chat history
        # updated_history = chat_history + [(question, generation)]

        return {"question": question, "generation": generation}

    def off_topic_response(self, state: AgentState):
        state["generation"] = self.llm_fallback(state)["generation"]
        # state["generation"] = "je ne peux pas répondre à cela"
        return state

    def document_grader(self, state: AgentState):
        docs = state["documents"]
        question = state["question"]

        system = """Vous êtes un évaluateur qui détermine la pertinence d'un document récupéré par rapport à une question utilisateur. \n
            Si le document contient des mots-clés ou une signification sémantique liée à la question, évaluez-le comme pertinent. \n
            Donnez une note binaire 'oui' ou 'non' pour indiquer si le document est pertinent pour la question."""

        grade_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system),
                (
                    "human",
                    "Document récupéré : \n\n {document} \n\n Question de l'utilisateur : {question}",
                ),
            ]
        )

        llm = self.llm_model
        structured_llm = llm.with_structured_output(GradeDocuments)
        grader_llm = grade_prompt | structured_llm
        scores = []
        for doc in docs:
            result = grader_llm.invoke({"document": doc, "question": question})
            scores.append(result.score)
        state["grades"] = scores
        return state

    def rewriter(self, state: AgentState):
        question = state["question"]
        system = """Vous êtes un réécrivain de questions qui convertit une question d'entrée en une meilleure version optimisée \n
            pour la récupération. Regardez l'entrée et essayez de raisonner sur l'intention sémantique / signification sous-jacente."""
        re_write_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system),
                (
                    "human",
                    "Voici la question initiale : \n\n {question} \n Formulez une question améliorée.",
                ),
            ]
        )
        llm = self.llm_model
        question_rewriter = re_write_prompt | llm | StrOutputParser()
        output = question_rewriter.invoke({"question": question})
        state["question"] = output
        return state

    def gen_router(self, state: AgentState):
        grades = state["grades"]
        print("NOTES DES DOCUMENTS :", grades)

        if any(grade.lower() == "oui" for grade in grades):
            filtered_grades = [grade for grade in grades if grade.lower() == "oui"]
            print("NOTES FILTRÉES DES DOCUMENTS :", filtered_grades)
            return "generate"
        else:
            return "rewrite_query"

    def generate_answer(self, state: AgentState):
        llm = self.llm_model
        question = state["question"]
        context = state["documents"]

        template = """Répondez à la question en vous basant uniquement sur le contexte suivant :

{context}

Question : {question}

Veuillez fournir la réponse en format Markdown.
        """

        prompt = ChatPromptTemplate.from_template(
            template=template,
        )
        chain = prompt | llm | StrOutputParser()
        result = chain.invoke({"question": question, "context": context})
        state["generation"] = result
        return state

    async def build_pipeline_flow(self):
        workflow = StateGraph(AgentState)

        workflow.add_node("topic_decision", self.question_classifier)
        workflow.add_node("off_topic_response", self.off_topic_response)
        workflow.add_node("retrieve_docs", self.retrieve_docs)
        workflow.add_node("rewrite_query", self.rewriter)
        workflow.add_node("generate_answer", self.generate_answer)
        workflow.add_node("document_grader", self.document_grader)

        workflow.add_edge("off_topic_response", END)
        workflow.add_edge("retrieve_docs", "document_grader")
        workflow.add_conditional_edges(
            "topic_decision",
            self.on_topic_router,
            {
                "on_topic": "retrieve_docs",
                "off_topic": "off_topic_response",
            },
        )
        workflow.add_conditional_edges(
            "document_grader",
            self.gen_router,
            {
                "generate": "generate_answer",
                "rewrite_query": "rewrite_query",
            },
        )
        workflow.add_edge("rewrite_query", "retrieve_docs")
        workflow.add_edge("generate_answer", END)

        workflow.set_entry_point("topic_decision")

        return workflow.compile()


class AgentState(TypedDict):
    question: str
    grades: list[str]
    generation: str
    documents: list[str]
    on_topic: bool


class GradeQuestion(BaseModel):
    """Boolean value to check whether a question is releated to the restaurant Bella Vista"""

    score: str = Field(
        description="Question is about restaurant? If yes -> 'Yes' if not -> 'No'"
    )


class GradeDocuments(BaseModel):
    """Boolean values to check for relevance on retrieved documents."""

    score: str = Field(
        description="Documents are relevant to the question, 'Yes' or 'No'"
    )

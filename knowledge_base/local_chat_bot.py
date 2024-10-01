import os
from typing import List, Tuple

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

from .ChatBot import RAGRetriever, GradeAnswer, RAGPipeline, web_search
from .weaviate_init import WeaviateConnector


class LocalChatBot(RAGPipeline):
    def __init__(self, config):
        # Load the configuration from the database

        assert config.llm_provider == 'ollama'
        self.llm_model = ChatOllama(model=config.model_name)

        preamble = config.model_preamble
        self.cohere_model = self.llm_model.bind(preamble=preamble)

        rag_preamble = config.model_preamble
        self.rag_cohere_model = self.llm_model.bind(preamble=rag_preamble)

        grad_preamble = config.grade_preamble
        self.grad_llm = self.llm_model

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
        hallucination_prompt = ChatPromptTemplate.from_messages(
            ("human", config.hallucination_prompt),
        )

        answer_preamble = config.answer_preamble
        self.answer_grader_llm = self.llm_model
        answer_prompt = ChatPromptTemplate.from_messages(
            [
                ("human", config.answer_prompt),
            ]
        )

        if config.embedding_provider == "ollama":
            self.embeddings_model = OllamaEmbeddings()
            self.embeddings_model.model = config.embedding_model
        elif config.embedding_provider == "cohere":
            self.embeddings_model = CohereEmbeddings()
            self.embeddings_model.model = config.embedding_model
        self.ocr_url = config.ocr_url
        self.ocr_api_key = config.ocr_api_key
        self.weaviate_client = WeaviateConnector().get_instance().client

        self.base_retriever = WeaviateVectorStore(self.weaviate_client,
                                                  "knowledge_base",
                                                  "answer",
                                                  attributes=['subject', 'question', 'answer'],
                                                  embedding=self.embeddings_model)

        self.secondary_retriever = WeaviateVectorStore(self.weaviate_client,
                                                       "pipeline_chunks",
                                                       "content",
                                                       embedding=self.embeddings_model).as_retriever()

        self.history_aware_retriever = create_history_aware_retriever(
            self.cohere_model, self.secondary_retriever, contextualize_q_prompt
        )

        self.rag_weaviate = self.weaviate_client.collections.get("knowledge_base")
        self.llm_chain = self.prompt | self.cohere_model | StrOutputParser()
        self.rag_chain = self.rag_prompt | self.rag_cohere_model | StrOutputParser()
        self.web_search_tool = TavilySearchResults()
        self.web_search_tool.api_wrapper = TavilySearchAPIWrapper()

        self.question_router = route_prompt | self.llm_model | StrOutputParser()
        self.hallucination_grader = hallucination_prompt | self.llm_model | StrOutputParser()
        self.answer_grader = answer_prompt | self.llm_model | StrOutputParser()

    def prompt(self, x):
        return ChatPromptTemplate.from_messages(
            [HumanMessage(
                f"Donnez une réponse concise à la question sans faire référence à aucun historique de conversation.{x['question']} \nRéponse : ")]
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
        self.secondary_retriever = WeaviateVectorStore(self.weaviate_client, index_name, text_name,
                                                       embedding=self.embeddings_model).as_retriever(
            search_kwargs={"filters": filters}
        )

    def retrieve_docs(self, state: AgentState):
        question = state["question"]

        base_documents = self.base_retriever.as_retriever().get_relevant_documents(query=question)
        print("BASE DOCUMENTS RETRIEVED:", base_documents)

        if base_documents:
            # Include metadata in the document representation
            state["documents"] = [
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata
                }
                for doc in base_documents
            ]
            state["retriever_used"] = "base"
        else:
            secondary_documents = self.secondary_retriever.get_relevant_documents(query=question)
            print("SECONDARY DOCUMENTS RETRIEVED:", secondary_documents)
            state["documents"] = [
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata
                }
                for doc in secondary_documents
            ]
            state["retriever_used"] = "secondary"

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
        structured_llm = llm.with_structured_output(GradeDocuments)
        grader_llm = prompt | structured_llm
        result = grader_llm.invoke({"question": question, "documents": documents})
        print(f"QUESTION et NOTE : {question} - {result.score if result else 'no'}")
        state["on_topic"] = result.score if result else 'non'
        return state

    def on_topic_router(self, state: AgentState):
        on_topic = state["on_topic"]
        if on_topic.lower() == "oui":
            return "on_topic"
        return "off_topic"

    def llm_fallback(self, state: AgentState):
        print("---LLM Fallback---")
        question = state["question"]
        chat_history = state["chat_history"]
        prompt = f"Historique de la conversation :\n{chat_history}\n\nQuestion actuelle : {question}\n\nRéponse :"
        generation = self.llm_chain.invoke({"question": prompt})
        state["generation"] = generation
        return state

    def off_topic_response(self, state: AgentState):
        state["generation"] = self.llm_fallback(state)["generation"]
        return state

    async def document_grader(self, state: AgentState):
        docs = state["documents"]
        question = state["question"]

        system = """
        Vous êtes un évaluateur qui détermine la pertinence d'un document récupéré par rapport à une question utilisateur.
        Si le document contient des mots-clés ou une signification sémantique liée à la question, évaluez-le comme pertinent.
        Donnez une note binaire 'oui' ou 'non' pour indiquer si le document est pertinent pour la question.
        **Répondez uniquement par 'oui' ou 'non', sans aucune explication supplémentaire.**
        """

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
            # print("Document:--------------", doc)
            result = None
            while result is None:
                result = await grader_llm.ainvoke({"document": doc, "question": question})
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
        print("DOCUMENT GRADES:", grades)

        if any(grade.lower() == "oui" for grade in grades):
            filtered_grades = [grade for grade in grades if grade.lower() == "oui"]
            print("FILTERED DOCUMENT GRADES:", filtered_grades)
            return "generate"
        elif state["retriever_used"] == "base":
            # If base retriever was used but no good matches, try secondary retriever
            return "use_secondary_retriever"
        else:
            # If secondary retriever was already used, pass to LLM directly
            return "llm_fallback"

    def generate_answer(self, state: AgentState):
        llm = self.llm_model
        question = state["question"]
        context = state["documents"]
        chat_history = state["chat_history"]
        template = """Répondez à la question en vous basant uniquement sur le contexte suivant :

    {context}

    Historique de conversation :
    {chat_history}

    Question : {question}

    Veuillez fournir la réponse en format Markdown et concise à la question sans faire référence à aucun historique de conversation..
    """

        prompt = ChatPromptTemplate.from_template(
            template=template,
        )
        chain = prompt | llm | StrOutputParser()
        result = chain.invoke({"question": question, "context": context, "chat_history": chat_history})
        state["generation"] = result
        return state

    def use_secondary_retriever(self, state: AgentState):
        question = state["question"]
        secondary_documents = self.secondary_retriever.get_relevant_documents(query=question)
        print("SECONDARY DOCUMENTS RETRIEVED:", secondary_documents)
        state["documents"] = [doc.page_content for doc in secondary_documents]
        state["retriever_used"] = "secondary"
        print("Sec Docs --------------------------", state["documents"])
        return state

    async def build_pipeline_flow(self):
        workflow = StateGraph(AgentState)

        # Update the workflow nodes and edges as needed
        workflow.add_node("topic_decision", self.question_classifier)
        workflow.add_node("off_topic_response", self.off_topic_response)
        workflow.add_node("retrieve_docs", self.retrieve_docs)
        workflow.add_node("generate_answer", self.generate_answer)
        workflow.add_node("document_grader", self.document_grader)
        workflow.add_node("use_secondary_retriever", self.use_secondary_retriever)
        workflow.add_node("llm_fallback", self.llm_fallback)

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
                "use_secondary_retriever": "use_secondary_retriever",
                "llm_fallback": "llm_fallback",
            },
        )
        workflow.add_edge("use_secondary_retriever", "document_grader")
        workflow.add_edge("generate_answer", END)
        workflow.add_edge("llm_fallback", END)

        workflow.set_entry_point("topic_decision")
        from IPython.display import Image, display
        from langchain_core.runnables.graph import CurveStyle, MermaidDrawMethod, NodeStyles

        # with open("architecture.png", "wb") as f:
        #     f.write(Image(
        #         workflow.compile().get_graph().draw_mermaid_png(
        #             draw_method=MermaidDrawMethod.API,
        #         )
        #     ).data)

        return workflow.compile()


class AgentState(TypedDict):
    question: str
    grades: list[str]
    generation: str
    documents: list[str]
    on_topic: bool
    retriever_used: str
    chat_history: List[Tuple[str, str]]


class GradeQuestion(BaseModel):
    """Valeur booléenne pour vérifier si une question est liée au restaurant Bella Vista"""

    score: str = Field(
        description="La question concerne-t-elle le restaurant ? Si oui -> 'oui' sinon -> 'non'"
    )


class GradeDocuments(BaseModel):
    """Valeurs booléennes pour vérifier la pertinence des documents récupérés."""

    score: str = Field(
        description="Les documents sont pertinents pour la question, 'oui' ou 'non'"
    )

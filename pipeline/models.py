import os
from django.db import models
from django.contrib.auth.models import User
from knowledge import models as knowledge_models
from cryptography.fernet import Fernet
from django.utils.functional import cached_property
from django.conf import settings
from encrypted_model_fields.fields import EncryptedTextField


class Pipeline(models.Model):
    creator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='pipelines',
        null=True,
        blank=True
    )
    name = models.CharField(max_length=255)
    description = models.TextField()
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    knowledge = models.ManyToManyField(knowledge_models.Knowledge)
    config = models.OneToOneField("RAGRetrieverConfig", on_delete=models.CASCADE, null=False, blank=False)

    def __str__(self):
        return self.name


class PipelineProgress(models.Model):
    pipeline = models.ForeignKey(Pipeline, on_delete=models.CASCADE)
    progress = models.IntegerField(default=0)
    status = models.CharField(max_length=50, default='pending')
    last_updated = models.DateTimeField(auto_now=True)


def default_args():
    return {'temperature': 0.0}


class tmp_EncryptedTextField(models.TextField):
    @cached_property
    def fernet(self):
        key = settings.ENCRYPTION_KEY.encode()
        return Fernet(key)

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        return self.fernet.decrypt(value.encode()).decode()

    def to_python(self, value):
        if isinstance(value, str):
            return value
        if value is None:
            return value
        return self.fernet.decrypt(value.encode()).decode()

    def get_prep_value(self, value):
        if value is None:
            return value
        return self.fernet.encrypt(value.encode()).decode()


class RAGRetrieverConfig(models.Model):
    model_choices = [
        ('cohere', 'Cohere'),
        ('anthropic', 'Anthropic'),
        ('gpt', 'GPT'),
        ('huggingface', 'HuggingFace'),
    ]
    embedding_choices = [
        ('cohere', 'Cohere'),
        ('gpt', 'GPT'),
        ('claude', 'Claude'),
        ('huggingface', 'HuggingFace'),
    ]

    llm_provider = models.CharField(max_length=50, choices=model_choices, default='cohere')
    model_name = models.CharField(max_length=100, default='command-r')
    model_args = models.JSONField(default=default_args)
    model_preamble = models.TextField(default="""
        Vous êtes un assistant pour les tâches d'assistance technique. 
        Utilisez les éléments de contexte récupérés et les exemples fournis pour répondre 
        à la question. Si vous ne connaissez pas la réponse, dites-le. 
        Utilisez trois phrases maximum et gardez la réponse concise. 
        Répondez toujours en français.
    """)
    grade_preamble = models.TextField(default="""
        Vous êtes un évaluateur évaluant la pertinence d'un document récupéré par rapport à une question d'utilisateur. 
        Si le document contient des mots-clés ou une signification sémantique liés à la question de l'utilisateur, évaluez-le comme pertinent. 
        Donnez une note binaire 'yes' ou 'no' pour indiquer si le document est pertinent par rapport à la question.
    """)
    grade_prompt = models.TextField(
        default="Document récupéré : \n\n {document} \n\n Question de l'utilisateur : {question}")
    route_question_preamble = models.TextField(default="""
        Prendre en compte l'historique de la conversation. Vous êtes un expert en routage de questions utilisateur vers un vectorstore ou une recherche Web.
        Le vectorstore contient des documents liés aux agents, à l'ingénierie des invites et aux attaques adversariales.
        Utilisez le vectorstore pour les questions sur ces sujets. Sinon, utilisez la recherche Web.
    """)
    enable_history = models.BooleanField(default=True)
    hallucination_preamble = models.TextField(default="""
        Vous êtes un évaluateur évaluant si une génération LLM est fondée sur / soutenue par un ensemble de faits récupérés. 
        Donnez une note binaire 'yes' ou 'no'. 'yes' signifie que la réponse est fondée sur / soutenue par l'ensemble des faits.
    """)
    hallucination_prompt = models.TextField(
        default="Ensemble de faits : \n\n {documents} \n\n Génération LLM : {generation}")
    embedding_provider = models.CharField(max_length=50, choices=embedding_choices, default='cohere')
    embedding_model = models.CharField(max_length=100, default='embed-multilingual-v3.0')
    embedding_args = models.JSONField(default=default_args)
    answer_preamble = models.TextField(default="""
        Vous êtes un évaluateur évaluant si une réponse répond / résout une question 
        Donnez une note binaire 'yes' ou 'no'. 'yes' signifie que la réponse résout la question.
    """)
    answer_prompt = models.TextField(
        default="Question de l'utilisateur : \n\n {question} \n\n Génération LLM : {generation}")
    ocr_url = models.URLField(default="https://api.llamacloud.ai/v1/pdf-extract")
    ocr_api_key = EncryptedTextField(default=os.getenv('COHERE_API_KEY'))
    model_api_key = EncryptedTextField(default=os.getenv('COHERE_API_KEY'))
    embedding_api_key = EncryptedTextField(default=os.getenv('COHERE_API_KEY'))

    def set_api_key(self, key_type, value):
        setattr(self, f'{key_type}_api_key', value)

    def get_api_key(self, key_type):
        return getattr(self, f'{key_type}_api_key')

    class Meta:
        verbose_name = "RAG Retriever Configuration"
        verbose_name_plural = "RAG Retriever Configurations"

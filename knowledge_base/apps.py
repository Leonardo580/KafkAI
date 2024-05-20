from django.apps import AppConfig
from . import weaviate_init

class BotKbConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'knowledge_base'

    def ready(self):
        weaviate_init.WeaviateConnector().get_instance().create_schema()



import weaviate
import weaviate.classes as wvc
from django.conf import settings


class WeaviateConnector:
    __instance = None
    __host = settings.WEAVIA_HOST
    __port = settings.WEAVIA_PORT

    @staticmethod
    def get_instance():

        if WeaviateConnector.__instance is None:
            WeaviateConnector.__instance = WeaviateConnector()
        return WeaviateConnector.__instance

    def __init__(self):
        self.client = weaviate.connect_to_local(WeaviateConnector.__host
                                                , WeaviateConnector.__port,
                                                headers={
                                                    "X-Cohere-Api-Key": settings.COHERE_API_KEY
                                                })

    def __del__(self):
        self.client.close()

    def create_schema(self):
        try:
            if self.client.collections.exists("knowledge_base"):
                self.client.collections.delete("knowledge_base")

            if self.client.collections.exists("tags"):
                self.client.collections.delete("tags")

            tags = self.client.collections.create(
                name="tags",
                description="A tag for categorizing knowledge base entries",
                vectorizer_config=wvc.config.Configure.Vectorizer.text2vec_cohere(),
                properties=[
                    wvc.config.Property(
                        name="name",
                        description="The name of the tag",
                        data_type=wvc.config.DataType.TEXT,
                        index_filterable=True,
                        vectorize_property_name=False,
                        tokenization=wvc.config.Tokenization.LOWERCASE

                    )
                ]
            )

            k = self.client.collections.create(
                name="knowledge_base",
                description="A knowledge base entry",
                vectorizer_config=wvc.config.Configure.Vectorizer.text2vec_cohere(),
                properties=[
                    wvc.config.Property(
                        name="subject",
                        description="The subject of the knowledge base entry",
                        data_type=wvc.config.DataType.TEXT,
                        index_filterable=True,
                        vectorize_property_name=True,
                        tokenization=wvc.config.Tokenization.LOWERCASE
                    ),
                    wvc.config.Property(
                        name="question",
                        description="The question of the knowledge base entry",
                        data_type=wvc.config.DataType.TEXT,
                        index_searchable=True,
                        vectorize_property_name=True,
                        tokenization=wvc.config.Tokenization.WHITESPACE
                    ),
                    wvc.config.Property(
                        name="answer",
                        description="The answer of the knowledge base entry",
                        data_type=wvc.config.DataType.TEXT,
                        index_searchable=True,
                        vectorize_property_name=True,
                        tokenization=wvc.config.Tokenization.WHITESPACE
                    )
                ],
                references=[
                    wvc.config.ReferenceProperty(
                        name="related_knowledge_base",
                        description="The related knowledge base entry",
                        target_collection="knowledge_base"
                    ),
                    wvc.config.ReferenceProperty(
                        name="tags",
                        description="The tags associated with the knowledge base entry",
                        target_collection="tags"
                    )
                ]
            )
            print("Tags created: ", tags.name)
            print("Knowledge base created: ", k.name)
        except Exception as e:
            print(f"Error creating schema: {e}")

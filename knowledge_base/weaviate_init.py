import weaviate
import weaviate.classes as wvc
from django.conf import settings
import wikipediaapi


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
        self.client = weaviate.connect_to_local(WeaviateConnector.__host,
                                                WeaviateConnector.__port,
                                                headers={
                                                    "X-Cohere-Api-Key": settings.COHERE_API_KEY
                                                })
        self.wiki_wiki = wikipediaapi.Wikipedia(language='fr', user_agent="mozilla")  # French Wikipedia

    def __del__(self):
        self.client.close()

    def create_schema(self):
        try:
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

            if self.client.collections.exists("knowledge_base"):
                self.client.collections.delete("knowledge_base")
                k = self.client.collections.create(
                    name="knowledge_base",
                    description="A knowledge base entry",
                    vectorizer_config=wvc.config.Configure.Vectorizer.text2vec_cohere(
                        model="embed-multilingual-v3.0",
                    ),
                    generative_config=wvc.config.Configure.Generative.cohere(
                        model="command-r",
                        temperature=0.2
                    ),

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
            print("Tags created: ")
            print("Knowledge base created: ")
        except Exception as e:
            print(f"Error creating schema: {e}")

    def create_dummy_data(self):

        # Insert dummy data into the "tags" collection
        tag1 = {"name": "Python"}
        tag2 = {"name": "Weaviate"}
        tags = self.client.collections.get("tags")
        with tags.batch.dynamic() as batch:
            batch.add_object(properties=tag1)
            batch.add_object(properties=tag2)

        # Insert dummy data into the "knowledge_base" collection
        kb_entry1 = {
            "subject": "Sage X3",
            "question": "What is Sage X3?",
            "answer": "Sage X3 is an Enterprise Resource Planning (ERP) software solution designed to manage various business processes, including finance, accounting, manufacturing, and customer relationship management.",
            # "tags": [tag1],
        }

        kb_entry2 = {
            "subject": "Inventory Management in Sage X3",
            "question": "How does Sage X3 handle inventory management?",
            "answer": "Sage X3 offers features for managing inventory levels, tracking stock movements, and optimizing stock replenishment. It allows you to define minimum and maximum stock levels, generate purchase orders based on demand, and track product lifecycles.",
            # "tags": [tag2],
            # "related_knowledge_base": [kb_entry1],
        }

        kb = self.client.collections.get("knowledge_base")
        with kb.batch.dynamic() as batch:
            batch.add_object(properties=kb_entry1)
            batch.add_object(properties=kb_entry2)

    def show_data(self):
        kb = self.client.collections.get("knowledge_base")
        print(kb)
        for tmp in kb.iterator():
            print(tmp.uuid, tmp.properties)

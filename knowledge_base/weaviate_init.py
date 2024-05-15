import weaviate
import weaviate.classes as wvc
client = weaviate.connect_to_local("localhost", port=8081)


client.collections.create(
    name="knowledge_base",
    vectorizer_config=wvc.config.Configure.Vectorizer.text2vec_cohere(),
    properties=[
        wvc.config.Property(
            name="subject",
            data_type=wvc.config.DataType.TEXT,
            vectorize_property_name=True,
            tokenization=wvc.config.Tokenization.LOWERCASE
        ),

    ]
)

from django.db import models
from django.contrib.auth.models import User
from knowledge import models as knowledge_models


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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class SimplePipeline(models.Model):
    pipeline = models.OneToOneField('Pipeline', on_delete=models.CASCADE, related_name='pipeline')
    instruction = models.TextField()
    variable = models.CharField(max_length=255)
    knowledge = models.ManyToManyField(knowledge_models.Knowledge, blank=True, related_name='knowledge')
    config = models.OneToOneField('PipelineConfig', on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.pipeline.name}"


class EmbeddingConfig(models.Model):
    embedding = models.CharField(max_length=255, default="embed-multilingual-v3.0")
    embedding_size = models.IntegerField(default=1024)
    api_key = models.CharField(max_length=255, default=None)

    def __str__(self):
        return f"{self.pipeline.name} Embedding Config"


class ModelConfig(models.Model):
    model = models.CharField(max_length=255, default="command-r")
    temperature = models.FloatField(default=0.2)
    chunk_size = models.IntegerField(default=512)
    api_key = models.CharField(max_length=255, default=None)

    def __str__(self):
        return f"{self.pipeline.name} Model Config"


class PipelineConfig(models.Model):

    embedding_config = models.ForeignKey(EmbeddingConfig, on_delete=models.SET_NULL, related_name='config', null=True)
    model_config = models.ForeignKey(ModelConfig, on_delete=models.SET_NULL, related_name='config', null=True)
    top_k = models.IntegerField(default=0)
    search_method = models.CharField(max_length=255, default="knn")
    use_agent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.pipeline.name} Config"

from django.db import models

# Create your models here.

# models.py
from django.db import models


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)


class KnowledgeBase(models.Model):
    id= models.IntegerField(primary_key=True)
    subject = models.CharField(max_length=255)
    question = models.TextField()
    answer = models.TextField()
    related_knowledge_base = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True,
                                               related_name='related_knowledge_bases')
    tags = models.ManyToManyField(Tag, related_name='knowledge_bases', blank=True)

    def __str__(self):
        return self.subject

from django.db import models

# Create your models here.

# models.py
from django.db import models


class Issue(models.Model):
    # Define your Issue model fields here
    title = models.CharField(max_length=255)
    description = models.TextField()


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)


class KnowledgeBase(models.Model):
    subject = models.CharField(max_length=255)
    question = models.TextField()
    answer = models.TextField()
    related_issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name='knowledge_bases')
    tags = models.ManyToManyField(Tag, related_name='knowledge_bases')

    def __str__(self):
        return self.subject

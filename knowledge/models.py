from django.db import models
from django.contrib.auth.models import User


# Create your models here.
class Knowledge(models.Model):
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='knowledge')
    title = models.CharField(max_length=200)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class KnowledgeFile(models.Model):
    knowledge = models.ForeignKey(Knowledge, related_name='files', on_delete=models.CASCADE)
    file = models.FileField(upload_to='knowledge_files/')
    file_type = models.CharField(max_length=50, choices=[
        ('text', 'Text'),
        ('html', 'HTML'),
        ('pdf', 'PDF'),
        ('doc', 'Word Document'),
        ('xls', 'Excel Document'),
        ('csv', 'CSV Document'),
    ])

    def __str__(self):
        return f"{self.knowledge.title} - {self.file.name}"

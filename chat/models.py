from django.contrib.auth.models import User
from django.contrib.auth.models import User
from django.contrib.auth.models import User
from django.db import models


class Chat(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chats')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Chat #{self.id} (User: {self.user.username})"


class Message(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages')
    sender = models.CharField(max_length=10, choices=[('user', 'User'), ('llm', 'LLM')])
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message #{self.id} (Chat: {self.chat.id}, Sender: {self.sender})"

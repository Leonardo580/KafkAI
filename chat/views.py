from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View, DetailView
from django.contrib.auth.models import User
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from chat.models import Chat, Message
from chat.serializers import MessageSerializer, ChatSerializer


# Create your views here.


class CreateChat(View):
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        chat = Chat.objects.create(user=request.user)
        return redirect('chat', chat_id=chat.id)

    def get(self, request, *args, **kwargs):
        chat = Chat.objects.create(user=request.user)
        return render(request, 'chats/create_chat.html', {'chat_id': chat.id})


class ChatDetailView(View):
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, id):
        # chat_id = self.kwargs.get('id')
        chat = Chat.objects.get(id=id)
        messages = chat.messages.order_by('-created_at').reverse()[:10]
        return render(request, 'chats/chat_detail.html', {'messages': messages})


class MessagePagination(PageNumberPagination):
    page_size = 10


class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all().order_by('-created_at')
    serializer_class = MessageSerializer
    pagination_class = MessagePagination

    def list(self, request, *args, **kwargs):
        chat_id = kwargs.get('chat_id')
        queryset = Message.objects.filter(chat_id=chat_id).order_by('-created_at').reverse()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class ChatPagination(PageNumberPagination):
    page_size = 5


class ChatViewSet(viewsets.ModelViewSet):
    queryset = Chat.objects.all().order_by('-created_at')
    serializer_class = ChatSerializer
    pagination_class = ChatPagination

    def list(self, request, *args, **kwargs):
        user_id = request.user.id
        queryset = Chat.objects.filter(user_id=user_id).order_by("-created_at")
        page= self.paginate_queryset(queryset)
        if page is not None:
            serializer= self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

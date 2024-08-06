from starlette.requests import Request
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View, DetailView
from django.contrib.auth.models import User
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from .models import Chat
from knowledge_base.ChatBot import RAGRetriever
import json

from chat.models import Chat, Message
from chat.serializers import MessageSerializer, ChatSerializer
from pipeline.models import Pipeline

from django.core.cache import cache


# Create your views here.


class CreateChat(View):
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        chat = Chat.objects.create(user=request.user)
        return redirect('chat', chat_id=chat.id)

    def get(self, request, *args, **kwargs):
        pipeline_id = request.GET.get('pipeline_id')
        pipeline = get_object_or_404(Pipeline, id=pipeline_id)
        chat = Chat.objects.create(user=request.user, pipeline=pipeline)
        return render(request, 'chats/create_chat.html'
                      , {'chat_id': chat.id
                          , 'pipeline_name': pipeline.name})


class ChatDetailView(View):
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, id):
        # chat_id = self.kwargs.get('id')
        chat = Chat.objects.get(id=id)
        pipeline = chat.pipeline
        messages = chat.messages.order_by('-created_at')[:10]
        return render(request, 'chats/chat_detail.html', {'messages': messages[::-1]
            , 'pipeline_name': pipeline.name if pipeline else None})


class MessagePagination(PageNumberPagination):
    page_size = 10


class MessageViewSet(viewsets.ModelViewSet):
    # queryset = Message.objects.all().order_by('-created_at')[::-1]
    queryset = Message.objects.all().order_by('-created_at')
    serializer_class = MessageSerializer
    pagination_class = MessagePagination

    def list(self, request, *args, **kwargs):
        chat_id = kwargs.get('chat_id')
        total_messages = Message.objects.filter(chat_id=chat_id).count()

        # Get all messages except for the last 10
        messages = Message.objects.filter(chat_id=chat_id).order_by('-created_at')[10:]
        queryset = messages[::-1]
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
        queryset = Chat.objects.filter(user_id=user_id).order_by("-created_at")[10::]

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from .langserve_urls import (
    invoke_chat, stream_chat, get_input_schema,
    get_output_schema, get_config_schema
)


@csrf_exempt
@require_http_methods(["POST"])
def invoke(request, chat_id):
    data = json.loads(request.body)
    response = invoke_chat(chat_id, data)
    return JsonResponse(response)


@csrf_exempt
@require_http_methods(["POST"])
def stream(request, chat_id):
    data = json.loads(request.body)
    response = stream_chat(chat_id, data)
    return StreamingHttpResponse(response, content_type='text/event-stream')


@require_http_methods(["GET"])
def input_schema(request, chat_id):
    schema = get_input_schema(chat_id)
    return JsonResponse(schema)


@require_http_methods(["GET"])
def output_schema(request, chat_id):
    schema = get_output_schema(chat_id)
    return JsonResponse(schema)


@require_http_methods(["GET"])
def config_schema(request, chat_id):
    schema = get_config_schema(chat_id)
    return JsonResponse(schema)


@csrf_exempt
@require_http_methods(["POST"])
def create_chat(request):
    data = json.loads(request.body)
    chat = Chat.objects.create(**data)
    return JsonResponse({"chat_id": chat.id})

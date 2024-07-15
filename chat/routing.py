from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'^ws/chat/(?P<chat_id>\d+)/$', consumers.ChatConsumer.as_asgi(), name="chat_ws"),
    re_path(r'^ws/chat/(?P<chat_id>\d+)/invoke/$', consumers.ChatConsumer.as_asgi(), name="chat_invoke"),
    re_path(r'^ws/chat/(?P<chat_id>\d+)/batch/$', consumers.ChatConsumer.as_asgi(), name="chat_batch"),
    re_path(r'^ws/chat/(?P<chat_id>\d+)/stream/$', consumers.ChatConsumer.as_asgi(), name="chat_stream"),
    re_path(r'^ws/chat/(?P<chat_id>\d+)/stream_log/$', consumers.ChatConsumer.as_asgi(), name="chat_stream_log"),
    re_path(r'^ws/chat/(?P<chat_id>\d+)/input_schema/$', consumers.ChatConsumer.as_asgi(), name="chat_input_schema"),
    re_path(r'^ws/chat/(?P<chat_id>\d+)/output_schema/$', consumers.ChatConsumer.as_asgi(), name="chat_output_schema"),
    re_path(r'^ws/chat/(?P<chat_id>\d+)/config_schema/$', consumers.ChatConsumer.as_asgi(), name="chat_config_schema"),
]
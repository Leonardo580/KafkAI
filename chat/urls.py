from django.urls import path, include

from . import views
from rest_framework.routers import DefaultRouter, re_path

# from django_email_verification import urls as email_urls  # include the urls
default_router = DefaultRouter()
default_router.register("get", views.MessageViewSet, "api_message_pagination")


urlpatterns = [
    path('create_chat/', views.CreateChat.as_view(), name='create_chat'),
    path('api/<int:id>/', views.ChatDetailView.as_view(), name='api_chat'),
    path('api/messages/<int:chat_id>/', include(default_router.urls)),
    re_path(r'^api/chats/', views.ChatViewSet.as_view({'get': 'list'}), name='api_chat_pagination'),

]

from django.urls import path

from . import views

# from django_email_verification import urls as email_urls  # include the urls

urlpatterns = [

    path('create_chat/', views.CreateChat.as_view(), name='create_chat'),
    path('chat/<int:pk>/', views.ChatDetailView.as_view(), name='chat_view'),

]

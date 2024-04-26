from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.views.generic import View, DetailView

from chat.models import Chat


# Create your views here.


class CreateChat(View):
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        chat = Chat.objects.create(user=request.user)
        return redirect('chat', chat_id=chat.id)

    def get(self, request, *args, **kwargs):
        return render(request, 'chats/create_chat.html')


class ChatDetailView(LoginRequiredMixin, DetailView):
    model = Chat
    template_name = 'chats/chat_detail.html'
    context_object_name = 'chat'

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)

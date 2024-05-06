from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View, DetailView
from django.contrib.auth.models import User
from chat.models import Chat, Message


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
        messages = chat.messages.all()
        return render(request, 'chats/chat_detail.html', {'messages': messages})


@csrf_exempt
class CreateNewChatView(View):
    def post(self, request):
        user_id = request.POST.get('user_id')

        if user_id is None:
            return JsonResponse({'error': 'User ID is required'}, status=400)

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({'error': 'User does not exist'}, status=404)

        chat = Chat.objects.create(user=user)
        return JsonResponse({'chat_id': chat.id})

    def get(self, request):
        chat_history = Chat.objects.values('id', 'user__username')
        return JsonResponse(list(chat_history), safe=False)

# from viewflow import flow, frontend
# from viewflow.views import this, Flow
# from viewflow.flow.views import UpdateProcessView
# from django.urls import reverse_lazy
# from .models import Chat
#
# @flow.flow_func()
# def get_chat_messages(request, chat_id, start=0, limit=10):
#     chat = Chat.objects.get(id=chat_id)
#     messages = chat.messages.all().order_by('-created_at')[start:start+limit]
#     return {'messages': messages, 'next_start': start + limit}
#
# class ChatMessageFlow(Flow):
#     process_class = get_chat_messages
#
#     @frontend.lazy_dispatch
#     def get_initial_data(self, request, chat_id):
#         return {}
#
#     @frontend.lazy_dispatch
#     def get_context_data(self, request, chat_id, **kwargs):
#         context = super().get_context_data(request, **kwargs)
#         context['chat_id'] = chat_id
#         return context
#
#     @frontend.lazy_dispatch
#     def get_success_url(self, request, chat_id, **kwargs):
#         return reverse_lazy('chat_detail', kwargs={'id': chat_id})
#
#     @frontend.lazy_dispatch
#     def get_success_message(self, request, chat_id, **kwargs):
#         return 'Chat messages loaded successfully.'
#
# chat_message_flow = ChatMessageFlow()
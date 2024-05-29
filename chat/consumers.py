import json
import asyncio

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer

from chat.models import Chat, Message
from knowledge_base.ChatBot import RAGRetriever

class ChatConsumer(WebsocketConsumer):
    def connect(self):
        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        self.chat_group_name = f'chat_{self.chat_id}'
        async_to_sync(self.channel_layer.group_add)(
            self.chat_group_name,
            self.channel_name
        )
        self.accept()

    def send(self, text_data=None, bytes_data=None, close=False):
        super().send(text_data=text_data, bytes_data=bytes_data, close=close)

    def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        sender = data['sender']

        if sender == 'user':
            chat = Chat.objects.get(id=self.chat_id)
            user_message = Message.objects.create(chat=chat, sender=sender, content=message)
            llm_answer = RAGRetriever().generate_answer(message)
            llm_message = Message.objects.create(chat=chat, sender='llm', content=llm_answer)

            # Send the user's message to the chat group
            async_to_sync(self.channel_layer.group_send)(
                self.chat_group_name,
                {
                    'type': 'chat_message',
                    'message': llm_answer,
                    'sender': "llm",
                }
            )

            # # Generate and send LLM response
            # llm_response = "generate_response(message)"
            # async_to_sync(self.channel_layer.group_send)(
            #     self.chat_group_name,
            #     {
            #         'type': 'chat_message',
            #         'message': llm_response,
            #         'sender': 'llm',
            #     }
            # )

    def chat_message(self, event):
        message = event['message']
        sender = event['sender']

        self.send(text_data=json.dumps({
            'message': message,
            'sender': sender,
        }))
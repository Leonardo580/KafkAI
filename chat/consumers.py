import json
import asyncio
from asgiref.sync import async_to_sync, sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from chat.models import Chat, Message
from knowledge_base.ChatBot import RAGRetriever


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        self.chat_group_name = f'chat_{self.chat_id}'

        await self.channel_layer.group_add(
            self.chat_group_name,
            self.channel_name
        )

        await self.accept()

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        sender = data['sender']

        if sender == 'user':
            chat = await sync_to_async(Chat.objects.get)(id=self.chat_id)
            user_message = await sync_to_async(Message.objects.create)(chat=chat, sender=sender, content=message)

            # Generate answer asynchronously
            llm_answer = RAGRetriever().generate_answer(message)
            llm_message = await sync_to_async(Message.objects.create)(chat=chat, sender='llm', content=llm_answer)

            # Send the LLM's message to the chat group
            if llm_answer == "We are currently facing an issue with our servers. Please try again later.":
                await self.channel_layer.group_send(
                    self.chat_group_name,
                    {
                        'type': 'chat_message',
                        'message': llm_answer,
                        'sender': 'llm',
                    }
                )
            else:
                async for chunk in llm_answer.astream_events({'input': message}, version='v1'):
                    if chunk["event"] in ["on_parser_start", "on_parser_stream"]:
                        await self.channel_layer.group_send(
                            self.chat_group_name,
                            {
                                'type': 'chat_message',
                                'message': json.dumps(chunk),
                                'sender': 'llm',
                            }
                    )

    async def chat_message(self, event):
        message = event['message']
        sender = event['sender']

        await self.send(text_data=json.dumps({
            'message': message,
            'sender': sender,
        }))

    # @sync_to_async
    # def generate_answer_async(self, message):
    #     return RAGRetriever().generate_answer(message)






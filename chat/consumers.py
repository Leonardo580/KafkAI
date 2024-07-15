import json
from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from chat.models import Chat, Message
from knowledge_base.ChatBot import RAGRetriever, get_chat_history
from weaviate.classes.query import Filter
from langchain.load.dump import dumps
from langchain.schema import runnable


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        self.chat_group_name = f'chat_{self.chat_id}'

        await self.channel_layer.group_add(
            self.chat_group_name,
            self.channel_name
        )
        rag_retriever = RAGRetriever()
        chat = await Chat.objects.aget(id=self.chat_id)
        pipeline_id = await sync_to_async(lambda: chat.pipeline.id)()
        filters = Filter.by_property("knowledge_id").equal(pipeline_id)
        rag_retriever.set_custom_retriever("pipeline_chunks", "content", filters)
        self.llm_answer = RAGRetriever().build_pipeline_flow()

        await self.accept()

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action', 'chat')

        if action == 'chat':
            await self.handle_chat(data)
        elif action == 'invoke':
            await self.handle_invoke(data)
        elif action == 'batch':
            await self.handle_batch(data)
        elif action == 'stream':
            await self.handle_stream(data)
        elif action == 'stream_log':
            await self.handle_stream_log(data)
        elif action == 'input_schema':
            await self.handle_input_schema(data)
        elif action == 'output_schema':
            await self.handle_output_schema(data)
        elif action == 'config_schema':
            await self.handle_config_schema(data)

    async def handle_chat(self, data):
        message = data['message']
        sender = data['sender']

        if sender == 'user':
            chat = await sync_to_async(Chat.objects.get)(id=self.chat_id)
            user_message = await sync_to_async(Message.objects.create)(chat=chat, sender=sender, content=message)

            # Generate answer asynchronously
            llm_answer = self.llm_answer
            chat_history = await get_chat_history(self.chat_id)
            llm_message = {}
            pipeline_id = await sync_to_async(lambda: chat.pipeline.id)()

            # If llm_answer is a string, send it directly
            if isinstance(llm_answer, str):
                await self.send(text_data=json.dumps({
                    'message': llm_answer,
                    'sender': 'llm',
                }))
                await sync_to_async(Message.objects.create)(chat=chat, sender='llm', content=llm_answer)
            else:
                # If llm_answer is a stream, process chunks
                async for chunk in llm_answer.astream_events(
                        input={'question': message},
                        version='v1'
                ):
                    if chunk["metadata"].get("langgraph_node") in ["llm_fallback", "generate"]:
                        if chunk["event"] in ["on_chain_start", "on_chain_stream"]:
                            await self.send(text_data=json.dumps({
                                'message': dumps(chunk),
                                'sender': 'llm',
                            }))
                    llm_message = chunk
                if llm_message["data"].get("output", "") != "":
                    llm_message = llm_message["data"].get("output", "").get("generation", "")
                else:
                    llm_message = llm_message["data"].get("llm_fallback", "").get("generation", "")
                await sync_to_async(Message.objects.create)(chat=chat, sender='llm', content=llm_message)

    async def handle_invoke(self, data):
        input_data = data.get('input', {})
        result = await self.llm_answer.ainvoke(input_data)
        await self.send(text_data=json.dumps({
            'action': 'invoke',
            'result': result
        }))

    async def handle_batch(self, data):
        inputs = data.get('inputs', [])
        results = await self.llm_answer.abatch(inputs)
        await self.send(text_data=json.dumps({
            'action': 'batch',
            'results': results
        }))

    async def handle_stream(self, data):
        input_data = data.get('input', {})
        async for chunk in self.llm_answer.astream(input_data):
            await self.send(text_data=json.dumps({
                'action': 'stream',
                'chunk': chunk
            }))

    async def handle_stream_log(self, data):
        input_data = data.get('input', {})
        async for chunk in self.llm_answer.astream_log(input_data):
            await self.send(text_data=json.dumps({
                'action': 'stream_log',
                'chunk': chunk
            }))

    async def handle_input_schema(self, data):
        schema = self.llm_answer.input_schema.schema()
        await self.send(text_data=json.dumps({
            'action': 'input_schema',
            'schema': schema
        }))

    async def handle_output_schema(self, data):
        schema = self.llm_answer.output_schema.schema()
        await self.send(text_data=json.dumps({
            'action': 'output_schema',
            'schema': schema
        }))

    async def handle_config_schema(self, data):
        schema = self.llm_answer.config_schema.schema()
        await self.send(text_data=json.dumps({
            'action': 'config_schema',
            'schema': schema
        }))

    async def chat_message(self, event):
        message = event['message']
        sender = event['sender']

        await self.send(text_data=json.dumps({
            'message': message,
            'sender': sender,
        }))
import json
import pprint

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from chat.models import Chat, Message
from knowledge_base.ChatBot import RAGRetriever, get_chat_history, RAGRetrieverCacher
from knowledge_base.local_chat_bot import LocalChatBot
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
        self.chat = await Chat.objects.aget(id=self.chat_id)
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
        chat = await sync_to_async(Chat.objects.get)(id=self.chat_id)
        rag_config = await sync_to_async(lambda: chat.pipeline.config)()
        if rag_config.llm_provider == 'huggingface':
            await self.handle_chat_local(data)
        else:
            await self.handle_chat_cohere(data)

    async def handle_chat_cohere(self, data):
        message = data['message']
        sender = data['sender']
        config = {"configurable": {"thread_id": self.chat_id}}
        pipeline_id = await sync_to_async(lambda: self.chat.pipeline.id)()
        if sender == 'user':
            chat = await sync_to_async(Chat.objects.get)(id=self.chat_id)
            rag_config = await sync_to_async(lambda: chat.pipeline.config)()
            chat_history=[]
            if rag_config.enable_history:
                chat_history = await get_chat_history(self.chat_id)
            user_message = await sync_to_async(Message.objects.create)(chat=chat, sender=sender, content=message)
            ragretriver = RAGRetriever(rag_config)
            ragretriver.update_retriever("pipeline_chunks", "content", pipeline_id)
            # llm_answer = await RAGRetrieverCacher.get_or_compile_graph(ragretriver)
            llm_answer = await ragretriver.build_pipeline_flow()
            # Generate answer asynchronously
            # chat_history = [("human", "je m'appelle anas"), ("ai", "bonjour anas.")]
            llm_message = {}
            pipeline_id = await sync_to_async(lambda: chat.pipeline.id)()
            steps = set()
            async for chunk in llm_answer.astream_events(
                    input={'question': message, "chat_history": chat_history}, config=config,
                    version='v2'
            ):
                # Send updates for each node in the graph
                if "metadata" in chunk and "langgraph_node" in chunk["metadata"]:
                    node_name = chunk["metadata"]["langgraph_node"]
                    if node_name not in steps:
                        await self.send(text_data=json.dumps({
                            'message': node_name,
                            'sender': 'system',
                            'type': 'progress'
                        }))
                    steps.add(node_name)

                if chunk["metadata"].get("langgraph_node") in ["llm_fallback", "generate"] and chunk[
                    "tags"] == ["seq:step:2", "seq:step:1"]:
                    if chunk["event"] in ["on_chat_model_stream", "on_chat_model_start"]:
                        msg = chunk["data"].get("chunk", "")
                        msg = msg.content if not isinstance(msg, str) else msg
                        print(msg)
                        await self.send(text_data=json.dumps({
                            'message': msg,
                            'sender': 'llm',
                            'event': chunk["event"]
                        }))

                # Save the chunk to the file
                llm_message = chunk
            # Send final answer
            final_answer = find_key(llm_message, "generation")
            await self.send(text_data=json.dumps({
                'message': final_answer,
                'sender': 'llm',
                'type': 'final_answer'
            }))
            await sync_to_async(Message.objects.create)(chat=chat, sender='llm', content=final_answer)

    async def handle_chat_local(self, data):
        message = data['message']
        sender = data['sender']
        config = {"configurable": {"thread_id": self.chat_id}}
        pipeline_id = await sync_to_async(lambda: self.chat.pipeline.id)()
        if sender == 'user':
            chat = await sync_to_async(Chat.objects.get)(id=self.chat_id)
            user_message = await sync_to_async(Message.objects.create)(chat=chat, sender=sender, content=message)
            rag_config = await sync_to_async(lambda: chat.pipeline.config)()
            ragretriver = LocalChatBot(rag_config)
            ragretriver.update_retriever("pipeline_chunks", "content",
                                         Filter.by_property("knowledge_id").equal(pipeline_id))
            # llm_answer = await RAGRetrieverCacher.get_or_compile_graph(ragretriver)
            llm_answer = await ragretriver.build_pipeline_flow()
            # Generate answer asynchronously
            chat_history = await get_chat_history(self.chat_id)
            # chat_history = [("human", "je m'appelle anas"), ("ai", "bonjour anas.")]
            llm_message = {}
            pipeline_id = await sync_to_async(lambda: chat.pipeline.id)()
            steps = set()

            async for chunk in llm_answer.astream_events(
                    input={'question': message}, config=config,
                    version='v2'
            ):
                # Send updates for each node in the graph
                if "metadata" in chunk and "langgraph_node" in chunk["metadata"]:
                    node_name = chunk["metadata"]["langgraph_node"]
                    if node_name not in steps:
                        await self.send(text_data=json.dumps({
                            'message': node_name,
                            'sender': 'system',
                            'type': 'progress'
                        }))
                    steps.add(node_name)
                # print("1----", chunk["metadata"].get("langgraph_node") in ["off_topic_response", "generate_answer"])
                # print("2----", chunk["tags"], chunk["tags"] == ['seq:step:1', 'seq:step:2'])
                if chunk["metadata"].get("langgraph_node") in ["off_topic_response", "generate_answer"] and (chunk[
                    "tags"] == ["seq:step:1", "seq:step:2"] or chunk["tags"] == ["seq:step:2", "seq:step:1"]):
                    print(chunk)
                    if chunk["event"] in ["on_chat_model_stream", "on_chat_model_start"]:
                        msg = chunk["data"].get("chunk", "")
                        msg = msg.content if not isinstance(msg, str) else msg
                        await self.send(text_data=json.dumps({
                            'message': msg,
                            'sender': 'llm',
                            'event': chunk["event"]
                        }))

                llm_message = chunk

            # Send final answer
            final_answer = find_key(llm_message, "generation")
            await self.send(text_data=json.dumps({
                'message': final_answer,
                'sender': 'llm',
                'type': 'final_answer'
            }))
            await sync_to_async(Message.objects.create)(chat=chat, sender='llm', content=final_answer)

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


def find_key(d, key_to_find):
    if key_to_find in d:
        return d[key_to_find]
    for k, v in d.items():
        if isinstance(v, dict):
            result = find_key(v, key_to_find)
            if result is not None:
                return result
        elif isinstance(v, list):
            for item in v:
                result = find_key(item, key_to_find)
                if result is not None:
                    return result
    return None

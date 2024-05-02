import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        # Call your LLM model to generate the response
        response_generator = generate_response(message)
        async for chunk in response_generator:
            await self.send(text_data=json.dumps({'chunk': chunk}))


async def generate_response(message):
    # Your logic to call the LLM model and generate the response
    response = 'This is a sample response from the LLM.'
    # Yield the response in chunks
    for i in range(0, len(response), 10):
        chunk = response[i:i + 10]
        yield chunk

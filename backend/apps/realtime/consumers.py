from channels.generic.websocket import AsyncJsonWebsocketConsumer


class UpdatesConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def disconnect(self, code):
        pass

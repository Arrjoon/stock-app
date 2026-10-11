from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken

from apps.accounts.models import User
from apps.realtime.notify import GROUP


class UpdatesConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        if not await self._authenticated():
            await self.close(code=4401)
            return
        await self.channel_layer.group_add(GROUP, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        if self.channel_layer is not None:
            await self.channel_layer.group_discard(GROUP, self.channel_name)

    async def dashboard_event(self, event):
        await self.send_json(event["payload"])

    async def _authenticated(self) -> bool:
        raw = parse_qs(self.scope.get("query_string", b"").decode()).get("token", [""])[0]
        if not raw:
            return False
        return await _token_is_valid(raw)


@database_sync_to_async
def _token_is_valid(raw: str) -> bool:
    try:
        access = AccessToken(raw)
    except TokenError:
        return False
    return User.objects.filter(pk=access.get("user_id"), is_active=True).exists()

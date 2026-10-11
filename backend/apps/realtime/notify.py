import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction

logger = logging.getLogger(__name__)

GROUP = "dashboard"


def notify(event: str, **payload) -> None:
    """Send a small dashboard event after the current transaction commits."""
    message = {"event": event, **payload}

    def _send():
        layer = get_channel_layer()
        if layer is None:
            return
        try:
            async_to_sync(layer.group_send)(
                GROUP,
                {"type": "dashboard.event", "payload": message},
            )
        except Exception:  # noqa: BLE001
            logger.warning("Could not publish %s", event, exc_info=True)

    transaction.on_commit(_send)


def publish_update(event: str, **payload) -> None:
    """Existing crawler hook. Keeps the current event name."""
    notify(event, **payload)

import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

logger = logging.getLogger(__name__)

GROUP = "dashboard"


def publish_update(event: str, **payload) -> None:
    """Push a dashboard event. Failures are logged and do not break the caller."""
    layer = get_channel_layer()
    if layer is None:
        return
    message = {"event": event, **payload}
    try:
        async_to_sync(layer.group_send)(
            GROUP,
            {"type": "dashboard.event", "payload": message},
        )
    except Exception:  # noqa: BLE001
        logger.warning("Could not publish %s", event, exc_info=True)

import asyncio
from collections import defaultdict
import structlog

log = structlog.get_logger()

class EventBus:
    """Simple async pub/sub bus for proposal events."""
    def __init__(self):
        self.subscribers = defaultdict(list)
        self.queue = asyncio.Queue()

    def subscribe(self, event_type: str, handler):
        self.subscribers[event_type].append(handler)

    async def emit(self, event_type: str, **data):
        log.info("event.emit", event_type=event_type, data=data)
        for handler in self.subscribers[event_type]:
            asyncio.create_task(handler(**data))
        await self.queue.put((event_type, data))

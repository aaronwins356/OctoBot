import asyncio
from collections import defaultdict
import structlog

logger = structlog.get_logger()


class EventBus:
    """Asynchronous publish/subscribe bus for OctoBot core systems."""

    def __init__(self):
        # subscribers[event_type] -> [handlers]
        self.subscribers = defaultdict(list)
        self.queue = asyncio.Queue()
        self.running = False

    def subscribe(self, event_type: str, handler):
        """Register an async handler for a specific event type.
        Use '*' to receive all events.
        """
        if not asyncio.iscoroutinefunction(handler):
            raise TypeError(f"Handler for '{event_type}' must be async")
        self.subscribers[event_type].append(handler)
        logger.debug("eventbus.subscribe", event_type=event_type, handler=handler.__name__)

    async def emit(self, event_type: str, **data):
        """Emit an event to all listeners and push it onto the queue."""
        logger.info("event.emit", event_type=event_type, data=data)
        # Call specific and wildcard handlers
        handlers = self.subscribers.get(event_type, []) + self.subscribers.get("*", [])
        for handler in handlers:
            asyncio.create_task(self._safe_invoke(handler, event_type, data))
        await self.queue.put((event_type, data))

    async def _safe_invoke(self, handler, event_type, data):
        """Invoke a handler and catch any exception."""
        try:
            await handler(event_type=event_type, **data)
        except Exception as exc:
            logger.error("eventbus.handler_error", event=event_type, handler=handler.__name__, error=str(exc))

    def enable_global_logging(self):
        """Attach a listener that logs every emitted event in detail."""
        async def log_event(event_type, **kwargs):
            logger.info("event.emitted", event=event_type, payload=kwargs)
        self.subscribe("*", log_event)

    async def run_forever(self):
        """Optional consumer loop — can be used for debugging or persistence."""
        self.running = True
        logger.info("eventbus.started")
        while self.running:
            event_type, data = await self.queue.get()
            logger.debug("eventbus.dispatch", event_type=event_type, data=data)
            self.queue.task_done()

    async def stop(self):
        self.running = False
        logger.info("eventbus.stopped")

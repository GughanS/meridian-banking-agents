import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

import structlog

logger = structlog.get_logger(__name__)

EventHandler = Callable[[Any], Awaitable[None]]

class EventBus:
    def __init__(self):
        self._subscribers: dict[str, list[EventHandler]] = {}
        self._queue: asyncio.Queue = asyncio.Queue()
        self._worker_task = None

    def subscribe(self, topic: str, handler: EventHandler):
        if topic not in self._subscribers:
            self._subscribers[topic] = []
        self._subscribers[topic].append(handler)
        logger.info("Subscribed to topic", topic=topic, handler=handler.__name__)

    async def publish(self, topic: str, payload: Any):
        await self._queue.put((topic, payload))
        logger.debug("Published event", topic=topic)

    async def _worker(self):
        logger.info("Event bus worker started")
        while True:
            try:
                topic, payload = await self._queue.get()
                handlers = self._subscribers.get(topic, [])
                for handler in handlers:
                    try:
                        await handler(payload)
                    except Exception as e:
                        logger.error("Error in event handler", topic=topic, error=str(e))
                self._queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Event bus worker error", error=str(e))

    def start(self):
        if self._worker_task is None:
            self._worker_task = asyncio.create_task(self._worker())

    async def stop(self):
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
            self._worker_task = None
            logger.info("Event bus worker stopped")

event_bus = EventBus()

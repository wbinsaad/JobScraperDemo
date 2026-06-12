import asyncio
from typing import Any


class JobQueue:
    """
    Internal async queue used to decouple fetching from processing.
    """

    def __init__(self, maxsize: int = 1_000) -> None:
        self._queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=maxsize)

    async def enqueue(self, job: dict[str, Any]) -> None:
        await self._queue.put(job)

    async def dequeue(self) -> dict[str, Any]:
        return await self._queue.get()

    def mark_done(self) -> None:
        self._queue.task_done()

    async def wait_until_empty(self) -> None:
        await self._queue.join()

    def depth(self) -> int:
        return self._queue.qsize()
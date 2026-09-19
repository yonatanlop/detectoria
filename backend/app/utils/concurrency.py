import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, TypeVar

T = TypeVar("T")


class BoundedExecutor:
    """Runs CPU-bound callables in a small thread pool, rejecting work past a
    fixed concurrency limit instead of letting requests queue unboundedly on a
    2-OCPU VM."""

    def __init__(self, max_concurrency: int):
        self._executor = ThreadPoolExecutor(max_workers=max_concurrency)
        self._semaphore = asyncio.Semaphore(max_concurrency)

    async def run(self, func: Callable[..., T], *args) -> T:
        if self._semaphore.locked():
            raise BusyError("El servidor está ocupado analizando otro documento. Intentá de nuevo en unos segundos.")
        async with self._semaphore:
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(self._executor, func, *args)


class BusyError(Exception):
    pass

import asyncio
import os


class AsyncLogger:
    def __init__(self, filename, max_lines=1000):
        self.filename = filename
        self.queue = asyncio.Queue()
        self._task = None
        self._stop_event = asyncio.Event()
        self.max_lines = max_lines
        self._lines = []

        # Загрузить существующие строки из файла (если файл существует)
        if os.path.exists(self.filename):
            with open(self.filename, 'r', encoding='utf-8') as f:
                self._lines = f.read().splitlines()
            # Ограничить количество строк max_lines
            if len(self._lines) > self.max_lines:
                self._lines = self._lines[-self.max_lines:]

    async def _writer(self):
        while not self._stop_event.is_set() or not self.queue.empty():
            try:
                message = await asyncio.wait_for(self.queue.get(), timeout=0.1)
                self._lines.append(message)

                if len(self._lines) > self.max_lines:
                    self._lines = self._lines[-self.max_lines:]

                await asyncio.to_thread(self._write_file)

                self.queue.task_done()
            except asyncio.TimeoutError:
                continue

    def _write_file(self):
        with open(self.filename, 'w', encoding='utf-8') as f:
            f.write('\n'.join(self._lines) + '\n')

    async def start(self):
        self._task = asyncio.create_task(self._writer())

    async def stop(self):
        self._stop_event.set()
        await self.queue.join()
        if self._task:
            await self._task

    async def log(self, message):
        await self.queue.put(message)
